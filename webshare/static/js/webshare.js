function WebShare(host, port) {
    var self = this
        , url = 'ws://' + host + ':' + port
        ;

    // Socket creation
    this.socket = new WebSocket(url);
    this.socket.onmessage = this.onmessage.bind(this);
    this.socket.onopen = function () {
        self.getKey(function (ok, code, body) {
            self.key = body.key;
        });
    };

    // Functional callbacks
    this.callbacks = {};

    // Misc. callbacks
    this.onrelay = undefined;
    this.oncommanderror = undefined;

    this.key = undefined;
}

WebShare.prototype.onmessage = function (msg) {
    console.log("IN", msg.data);
    var data = JSON.parse(msg.data)
        , echo = data.echo
        , ok = data.ok
        , code = data.code
        , body = data.body
        , command = data.command
        , callbackId = echo.callbackId
        , callback
        ;

    console.log(callbackId, this.callbacks);

    if (code == 'COMMAND_ERROR') {
        if (self.oncommanderror) self.oncommanderror(ok, code, body);
    } else if (command == 'relay') {
        if (self.onrelay) self.onrelay(ok, code, body);
    } else if (callbackId) {
        callback = this.callbacks[callbackId];
        if (callback) {
            callback(ok, code, body);
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
        if (!this.callbacks[id]) {
            return id;
        }
    }
}

WebShare.prototype._command = function (command, body, callback) {
    var callbackId = this._generateCallbackId()
        , message = {echo: {callbackId: callbackId}, command: command, body: body}
        , package = JSON.stringify(message)
        ;
    this.callbacks[callbackId] = callback;
    console.log("OUT", package);
    this.socket.send(package);
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