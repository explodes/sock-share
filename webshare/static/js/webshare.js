function WebShare(host, port, debug) {
    var self = this
        , url = 'ws://' + host + ':' + port
        ;

    this.debug = debug || false;

    // Socket creation
    this._socket = new WebSocket(url);
    this._socket.onmessage = this.onmessage.bind(this);
    this._socket.onopen = function () {
        self.getKey(function (ok, code, body) {
            self.key = body.key;
        });
    };

    // Functional callbacks
    this._callbacks = {};

    // Misc. callbacks
    this.onrelay = undefined; // information was relayed :: f(true, 'SUCCESS', packageObject)
    this.oncommanderror = undefined; // invalid command stuff :: f(false, 'COMMAND_ERROR', {error: message})
    this.onunpair = undefined; // involuntary unpair :: f(success, code, null)

    this.key = undefined;
    this.pairedTo = undefined;
}

WebShare.prototype.onmessage = function (msg) {
    if (this.debug) console.log(this.key, "IN", msg.data);
    var data = JSON.parse(msg.data)
        , echo = data.echo
        , ok = data.ok
        , code = data.code
        , body = data.body
        , command = data.command
        , callbackId = echo ? echo.callbackId : null
        , callback
        ;
    if (code == 'COMMAND_ERROR') {
        if (this.oncommanderror) this.oncommanderror(ok, code, body);
    } else if (command == 'relay') {
        if (this.onrelay) this.onrelay(ok, code, body);
    } else if (callbackId) {
        callback = this._callbacks[callbackId];
        if (callback) {
            callback(ok, code, body);
        }
    } else if (command == 'unpair') {
        // involuntary unpair (unpair w/o callbackId)
        if (this.onunpair) this.onunpair(ok, code, body);
    }

    // Track pair status
    if (ok && code == 'SUCCESS') {
        if (command == 'pair') {
            this.pairedTo = body.with;
        } else if (command == 'unpair') {
            this.pairedTo = undefined;
        }
    }
}

WebShare.prototype._generateCallbackId = function () {
    var possible = 'abcdef1234567890'
        , id
        ;
    while (true) {
        id = '';
        for (var i = 0; i < 7; i++) {
            id += possible.charAt(Math.floor(Math.random() * possible.length));
        }
        if (!this._callbacks[id]) {
            return id;
        }
    }
}

WebShare.prototype._command = function (command, body, callback) {
    var callbackId = this._generateCallbackId()
        , message = {echo: {callbackId: callbackId}, command: command, body: body}
        , package = JSON.stringify(message)
        ;
    this._callbacks[callbackId] = callback;
    if (this.debug) console.log(this.key, "OUT", package);
    this._socket.send(package);
}

WebShare.prototype.pair = function (target, callback) {
    this._command('pair', {target: target}, callback);
}

WebShare.prototype.unpair = function (message, callback) {
    this._command('unpair', undefined, callback);
}

WebShare.prototype.relay = function (message, callback) {
    this._command('relay', message, callback);
}

WebShare.prototype.getKey = function (callback) {
    this._command('key', undefined, callback);
}