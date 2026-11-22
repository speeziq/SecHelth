package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"net"
	"os"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

type response struct {
	OK     bool        `json:"ok"`
	Data   interface{} `json:"data,omitempty"`
	Error  string      `json:"error,omitempty"`
	Engine string      `json:"engine"`
}

var commonPorts = map[int]string{
	21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS", 80: "HTTP",
	110: "POP3", 143: "IMAP", 443: "HTTPS", 445: "SMB", 993: "IMAPS",
	995: "POP3S", 3306: "MySQL", 3389: "RDP", 5432: "PostgreSQL",
	6379: "Redis", 8080: "HTTP-Alt", 8443: "HTTPS-Alt", 27017: "MongoDB",
}

func emit(ok bool, data interface{}, err string) {
	out := response{OK: ok, Data: data, Error: err, Engine: "go"}
	if !ok {
		out.Data = nil
	}
	_ = json.NewEncoder(os.Stdout).Encode(out)
}

func resolve(host string) {
	host = strings.TrimSpace(host)
	if host == "" {
		emit(false, nil, "Input is empty")
		return
	}
	ips, err := net.LookupIP(host)
	if err != nil {
		emit(false, nil, fmt.Sprintf("Could not resolve %q: %v", host, err))
		return
	}
	seen := map[string]bool{}
	values := make([]string, 0, len(ips))
	for _, ip := range ips {
		text := ip.String()
		if !seen[text] {
			seen[text] = true
			values = append(values, text)
		}
	}
	sort.Strings(values)
	emit(true, values, "")
}

func reverse(host string) {
	names, err := net.LookupAddr(strings.TrimSpace(host))
	if err != nil {
		emit(false, nil, fmt.Sprintf("No reverse DNS record found for %q", host))
		return
	}
	emit(true, names, "")
}

func parsePorts(text string) ([]int, error) {
	text = strings.TrimSpace(text)
	if text == "" {
		ports := make([]int, 0, len(commonPorts))
		for port := range commonPorts {
			ports = append(ports, port)
		}
		sort.Ints(ports)
		return ports, nil
	}
	values := []int{}
	seen := map[int]bool{}
	add := func(port int) error {
		if port < 1 || port > 65535 {
			return fmt.Errorf("ports must be between 1 and 65535")
		}
		if !seen[port] {
			seen[port] = true
			values = append(values, port)
		}
		return nil
	}
	for _, part := range strings.Split(text, ",") {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}
		if strings.Contains(part, "-") {
			bounds := strings.SplitN(part, "-", 2)
			start, err1 := strconv.Atoi(strings.TrimSpace(bounds[0]))
			end, err2 := strconv.Atoi(strings.TrimSpace(bounds[1]))
			if err1 != nil || err2 != nil || start > end {
				return nil, fmt.Errorf("invalid port range %q", part)
			}
			if end-start+1 > 5000 {
				return nil, fmt.Errorf("please scan at most 5000 ports at a time")
			}
			for port := start; port <= end; port++ {
				if err := add(port); err != nil {
					return nil, err
				}
			}
		} else {
			port, err := strconv.Atoi(part)
			if err != nil {
				return nil, fmt.Errorf("invalid port %q", part)
			}
			if err := add(port); err != nil {
				return nil, err
			}
		}
	}
	if len(values) == 0 {
		return nil, fmt.Errorf("no ports provided")
	}
	if len(values) > 5000 {
		return nil, fmt.Errorf("please scan at most 5000 ports at a time")
	}
	sort.Ints(values)
	return values, nil
}

func scan(host, portText string, timeoutMillis int, workers int) {
	host = strings.TrimSpace(host)
	if host == "" {
		emit(false, nil, "Input is empty")
		return
	}
	ports, err := parsePorts(portText)
	if err != nil {
		emit(false, nil, err.Error())
		return
	}
	ip := host
	if net.ParseIP(host) == nil {
		ips, err := net.LookupIP(host)
		if err != nil || len(ips) == 0 {
			emit(false, nil, fmt.Sprintf("Could not resolve %q", host))
			return
		}
		ip = ips[0].String()
	}
	if workers < 1 {
		workers = 1
	}
	if workers > 1000 {
		workers = 1000
	}
	timeout := time.Duration(timeoutMillis) * time.Millisecond
	jobs := make(chan int)
	open := make(chan int)
	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for port := range jobs {
				address := net.JoinHostPort(ip, strconv.Itoa(port))
				conn, err := net.DialTimeout("tcp", address, timeout)
				if err == nil {
					_ = conn.Close()
					open <- port
				}
			}
		}()
	}
	go func() {
		for _, port := range ports {
			jobs <- port
		}
		close(jobs)
		wg.Wait()
		close(open)
	}()
	found := make([]int, 0)
	for port := range open {
		found = append(found, port)
	}
	sort.Ints(found)
	portsFound := make([]map[string]interface{}, 0, len(found))
	for _, port := range found {
		service, exists := commonPorts[port]
		if !exists {
			service = "unknown"
		}
		portsFound = append(portsFound, map[string]interface{}{"port": port, "service": service})
	}
	emit(true, map[string]interface{}{
		"host": host, "ip": ip, "ports_scanned": len(ports),
		"open_ports": portsFound,
	}, "")
}

func main() {
	if len(os.Args) < 2 {
		emit(false, nil, "Missing command")
		return
	}
	command := os.Args[1]
	switch command {
	case "resolve":
		fs := flag.NewFlagSet(command, flag.ExitOnError)
		host := fs.String("host", "", "host name")
		_ = fs.Parse(os.Args[2:])
		resolve(*host)
	case "reverse":
		fs := flag.NewFlagSet(command, flag.ExitOnError)
		host := fs.String("host", "", "IP address")
		_ = fs.Parse(os.Args[2:])
		reverse(*host)
	case "scan":
		fs := flag.NewFlagSet(command, flag.ExitOnError)
		host := fs.String("host", "", "host name or IP")
		ports := fs.String("ports", "", "port list or range")
		timeout := fs.Int("timeout-ms", 1000, "connection timeout")
		workers := fs.Int("workers", 400, "concurrent workers")
		_ = fs.Parse(os.Args[2:])
		scan(*host, *ports, *timeout, *workers)
	case "version":
		emit(true, map[string]string{"version": "1.0.0"}, "")
	default:
		emit(false, nil, "Unknown command")
	}
}
