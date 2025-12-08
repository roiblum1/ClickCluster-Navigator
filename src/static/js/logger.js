// Logger utility for OpenShift Cluster Navigator
// Provides structured logging with levels and timestamps

const LogLevel = {
    DEBUG: 0,
    INFO: 1,
    WARN: 2,
    ERROR: 3,
    NONE: 4
};

class Logger {
    constructor(name, level = LogLevel.INFO) {
        this.name = name;
        this.level = level;
        this.colors = {
            DEBUG: '#6c757d',
            INFO: '#0dcaf0',
            WARN: '#ffc107',
            ERROR: '#dc3545'
        };
    }

    setLevel(level) {
        this.level = level;
    }

    _log(level, levelName, message, ...args) {
        if (level < this.level) return;

        const timestamp = new Date().toISOString();
        const prefix = `[${timestamp}] [${levelName}] [${this.name}]`;
        const color = this.colors[levelName];

        switch (levelName) {
            case 'DEBUG':
                console.debug(`%c${prefix}`, `color: ${color}`, message, ...args);
                break;
            case 'INFO':
                console.info(`%c${prefix}`, `color: ${color}`, message, ...args);
                break;
            case 'WARN':
                console.warn(`%c${prefix}`, `color: ${color}`, message, ...args);
                break;
            case 'ERROR':
                console.error(`%c${prefix}`, `color: ${color}`, message, ...args);
                break;
        }
    }

    debug(message, ...args) {
        this._log(LogLevel.DEBUG, 'DEBUG', message, ...args);
    }

    info(message, ...args) {
        this._log(LogLevel.INFO, 'INFO', message, ...args);
    }

    warn(message, ...args) {
        this._log(LogLevel.WARN, 'WARN', message, ...args);
    }

    error(message, ...args) {
        this._log(LogLevel.ERROR, 'ERROR', message, ...args);
    }

    // Log API calls
    apiCall(method, url, data = null) {
        this.debug(`API ${method}`, url, data || '');
    }

    // Log API responses
    apiResponse(method, url, status, data = null) {
        if (status >= 200 && status < 300) {
            this.debug(`API ${method} ${status}`, url, data || '');
        } else if (status >= 400) {
            this.error(`API ${method} ${status}`, url, data || '');
        }
    }

    // Log user actions
    userAction(action, details = null) {
        this.info(`User Action: ${action}`, details || '');
    }

    // Performance logging
    performance(operation, duration) {
        this.debug(`Performance: ${operation} took ${duration}ms`);
    }
}

// Create loggers for different modules
const loggers = {
    app: new Logger('App'),
    api: new Logger('API'),
    auth: new Logger('Auth'),
    dashboard: new Logger('Dashboard'),
    ui: new Logger('UI')
};

// Set log level based on environment
// In production, you might want to set this to LogLevel.WARN or LogLevel.ERROR
const isDevelopment = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const defaultLevel = isDevelopment ? LogLevel.DEBUG : LogLevel.INFO;

Object.values(loggers).forEach(logger => logger.setLevel(defaultLevel));

// Export for use in other modules
window.Logger = Logger;
window.LogLevel = LogLevel;
window.loggers = loggers;
