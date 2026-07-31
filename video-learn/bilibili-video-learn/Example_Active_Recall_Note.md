The Purpose of Log

```ad-success
1. Debug the production problem/bug
2. To Monitoring
3. Used For Business Statistic
```

Add These Two Dependencies for log

```go
rotatelogs "github.com/lestrrat-go/file-rotatelogs"
"github.com/sirupsen/logrus"
```

1. Write a InitLogrus Function in logrus.go
   1. Parameter: logFile, level
   2. Return: pointer of logrus.Logger
2. InitLogrus
   1. Creating a logger
   2. Set the Level of Display
   3. Create a Plain Format
      1. Force Display Color <- comment it
      2. Force Not Display Color
      3. Timestamp in yyyy-mm-dd hh:mm:ss.ms
   4. Create a JSON Format
      1. Timestamp in yyyy-mm-dd hh:mm:ss.ms
   5. Create a rotatelog
      1. fileName = logrus.log.yyyymmddHH
      2. Create softlink file for newest log file
      3. Every 1 hr will create new log file
      4. Only kept 7 days log
   6. Set to print to file
   7. Log Include func and file
   8. Add Hook with Custom AppHook with AppName propertie
      1. Levels include Error, Fatal, Panic
      2. Fire
         1. UPDATE the logrus.Entry["app"]
         2. READ(PRINT) logrus.Entry. EG: Error, Fatal and Panic log
   9. Create a TestLogrus in logrus_test.go
   10. invoke InitLogrus
       1. log directory log/logrus.log
       2. level info
   11. Logger -> print this is debug log
   12. create log entry with
       1. name: "testLogrus"
       2. age: 24
   13. use log entry print "this is info log"
   14. use log entry print "this is warn log, float-3.140"
   15. Logger -> print this is errorlog1this is error log 2
   16. Logger -> print "this is fatal log" (What would happens)
   17. Logger -> print "this is panic log" (What would happens)

Terminal Output:

```sh
go test -v . -run='^TestLogrus$' -count=1
=== RUN   TestLogrus
this is error log1this is error log2
this is panic log
--- PASS: TestLogrus (0.00s)
PASS
ok      fulim/logs      0.006s
```

File Output:

```log
time="2026-07-22 10:29:35.407" level=info msg="this is info log" func=fulim/logs.TestLogrus file="/home/fulim/go-logrus/logrus_test.go:13" age=24 name=testLogrus
time="2026-07-22 10:29:35.408" level=warning msg="this is warn log, float-3.140" func=fulim/logs.TestLogrus file="/home/fulim/go-logrus/logrus_test.go:14" age=24 name=testLogrus
time="2026-07-22 10:29:35.408" level=error msg="this is error log1this is error log2" func=fulim/logs.TestLogrus file="/home/fulim/go-logrus/logrus_test.go:15" app=logrus
time="2026-07-22 10:29:35.408" level=panic msg="this is panic log" func=fulim/logs.TestLogrus file="/home/fulim/go-logrus/logrus_test.go:21" app=logrus

```

````ad-success
`logrus.go`
```go
package logrus

import (
	"fmt"
	"strings"
	"time"

	rotatelogs "github.com/lestrrat-go/file-rotatelogs"
	"github.com/sirupsen/logrus"
)

func InitLogrus(logFile, level string) *logrus.Logger {
	logger := logrus.New()
	switch strings.ToLower(level) {
	case "debug":
		logger.SetLevel(logrus.DebugLevel)
	case "info":
		logger.SetLevel(logrus.InfoLevel)
	case "warn":
		logger.SetLevel(logrus.WarnLevel)
	case "error":
		logger.SetLevel(logrus.ErrorLevel)
	case "fatal":
		logger.SetLevel(logrus.FatalLevel)
	case "panic":
		logger.SetLevel(logrus.PanicLevel)
	default:
		panic(fmt.Errorf("Invalid log level %s", level))
	}

	// Plain Format
	logger.SetFormatter(&logrus.TextFormatter{
		// ForceColors: true, // Force Display Color (Only works for some terminal)
		DisableColors:   true,                      // Force Not Display Color
		TimestampFormat: "2006-01-02 15:04:05.000", // Display ms
	})

	// JSON Format
	// logger.SetFormatter(&logrus.JSONFormatter{
	// 	TimestampFormat: "2006-01-02 15:04:05.000", // Display ms
	// })

	file, err := rotatelogs.New(
		logFile+".%Y%m%d%H",                      //Specific the directory and file name, if don't have the file, will create new file
		rotatelogs.WithLinkName(logFile),         // Create softlink file for newest log file
		rotatelogs.WithRotationTime(1*time.Hour), // Every 1 hr will create new log file
		rotatelogs.WithMaxAge(7*24*time.Hour),    // Only kept 7 days log, OR can use WithRotationCount to kept the few recent log file
	)
	if err != nil {
		panic(err)
	}
	logger.SetOutput(file) // Set to print to file
	// logger.SetOutput(os.Stdout) // Set to print to terminal
	logger.SetReportCaller(true)                // Log Include func and file
	logger.AddHook(&AppHook{AppName: "logrus"}) // Before Output the log, Execute the hook

	return logger
}

// To satify logrus.Hook Interface, have to implement
// 1. (h *AppHook) Levels() []logrus.Level
// 2. (h *AppHook) Fire(entry *logrus.Entry) error
type AppHook struct {
	AppName string
}

// Hook Only works for what level
func (h *AppHook) Levels() []logrus.Level {
	return []logrus.Level{
		logrus.ErrorLevel,
		logrus.FatalLevel,
		logrus.PanicLevel,
	}
}

// When Fire the function, it can READ or UPDATE the logrus.Entry
func (h *AppHook) Fire(entry *logrus.Entry) error {
	entry.Data["app"] = h.AppName // UPDATE the logrus.Entry
	fmt.Println(entry.Message)    // READ logrus.Entry. EG: Error, Fatal and Panic log will send to logstash, kafka
	return nil
}

```

`logrus_test.go`
```go
package logrus

import (
	"testing"

	"github.com/sirupsen/logrus"
)

func TestLogrus(t *testing.T) {
	logger := InitLogrus("./log/logrus.log", "info")
	logger.Debug("this is debug log")
	logEntry := logger.WithFields(logrus.Fields{"name": "testLogrus", "age": 24}) // Carry Extra key value pair
	logEntry.Info("this is info log")
	logEntry.Warnf("this is warn log, float-%.3f", 3.14)     // Printf Formating
	logger.Error("this is error log1", "this is error log2") // Multiple Message

	// logger.Fatal("this is fatal log") // After writing log, will call os.Exit(1)
	defer func() {
		recover()
	}()
	logger.Panic("this is panic log") // After writing log, will call panic
}

// go test -v . -run='^TestLogrus$' -count=1

```
````
