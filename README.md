sock-share
==========

Pair two clients together via websockets.

./manage.py share_server
------------------------

First, run the share server:

```
./manage.py share_server --host=192.168.1.3 --port=9000

```

webshare.js
-----------

Example usage:


function logIt(success, code, body) { console.log(success, code, body); }

var alice = new WebShare('192.168.1.3', 9000);
var bob = new WebShare('192.168.1.3', 9000);

alice.onrelay = logIt; // when a message is relayed to us
alice.oncommanderror = logIt; // underlying framework error
alice.onunpair = logIt; // involuntary unpair

bob.onrelay = logIt; // when a message is relayed to us
bob.oncommanderror = logIt; // underlying framework error
bob.onunpair = logIt; // involuntary unpair

function testThem() {

}
s.pair(j.key);

