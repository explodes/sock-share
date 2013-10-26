sock-share
==========

Pair two clients together via websockets.


Lets say your favorite browser can be controlled by your favorite phone.
You need to make a connection somehow.

# Enter webshare.js

class WebShare
--------------

This class contains the functionality for pairing, unparing, and relaying information to its paired partner.
Callbacks are used to handle this functionality.
Handling relays is up to client implemenations.


### Constructors:

#### `new WebShare(host, port, debugMode=false)`

Construct a new instance connection to `host` and `port` optionally enabling `debugMode` which just enables logging.

### Properties:

#### `onrelay`
Callback function when data is relayed to us from our paired partner.


Signature: `function(true, 'RELAY_OK', packageObject)`

#### `oncommanderror`
Callback function when the underlying framework fails to support itself.
Clients do not need to worry about this, although it may help with debugging.


Signature: `function(false, 'COMMAND_ERROR', {error: message})`

#### `onunpair`
Callback function when unpairing happens involuntarily, either the paired partner disconnected by error or gracefully.


Signature: `function(true, 'SUCCESS', null)`

#### `key`
Identification of this WebShare instance, used for pairing

#### `pairedTo`
Identification of the paired partner

#### `debug`
Show logging messages

### Methods:

All callbacks are in the form of `function(success, code, body)`

#### `pair(key, callback)`
Pair this `WebShare` with another. Pairing with or to an already paired or non-existant partner will result in an error code. You cannot pair with yourself.

#### `unpair(callback)`
Unpair this `WebShare` from its partner. Unpairing unpaired `WebShares` will result in error.

#### `relay(data, callback)`
Relay information to the paired partner. The callback will be called but the data sent will not be included.

#### `getKey(callback)`
Simply acquires this `WebShare`'s key from the server. This happens automatically on instantiation, although it is not instant. Get the key by accessing the `key` property.

### `close()`
Close the underlying WebSocket.


### Example

Here is an example of Alice pairing with Bob.



```
function logger(name, action) {
    return function(success, code, body) {
        console.log(name, action, success, code, body);
    }
}

var debug = false;

var alice = new WebShare('192.168.1.3', 9000, debug);
var bob = new WebShare('192.168.1.3', 9000, debug);

alice.oncommanderror = logger('Alice', 'oncommanderror');
alice.onunpair = logger('Alice', 'onunpair');
alice.onrelay = logger('Alice', 'onrelay');

bob.oncommanderror = logger('Bob', 'oncommanderror');
bob.onunpair = logger('Bob', 'onunpair');
bob.onrelay = function(success, code, body) {
    logger('bob', 'onrelay')(success, code, body);
    var name = body.hello;
    if (name != bob) {
        bob.relay('my name isnt ' + name + ' its bob!');
    } else {
        bob.relay([123, 'hello alice!']); // can relay anything
    }
}


function testThem() {
    alice.pair(bob.key, function(success, code, body) {
        if (!success) { return; }
        console.log('Alice (' + alice.key + ') is paired to Bob (' + alice.pairedTo + ')');
        alice.relay({hello: 'dan'}, function(success, code, body) {
            console.log('Alice is done with the relay');
        });
    });
}

setTimeout(testThem, 1000); // wait for each person to obtain their keys so that they can be paired in code.
```

That example puts the following in the console:

```
Alice (ae4321aa) is paired to Bob (c9053d5b)
bob onrelay true RELAY_OK Object {hello: "dan"}
Alice is done with the relay
Alice onrelay true RELAY_OK my name isnt dan its bob!
```


Running the server
------------------

TODO: Make a more portable way...

./manage.py share_server (As a django app)
------------------------------------------

First, run the share server:

```
./manage.py share_server --host=192.168.1.3 --port=9000

```
