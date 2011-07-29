var Cc = Components.classes;
var Ci = Components.interfaces;

Components.utils.import("resource://gre/modules/XPCOMUtils.jsm");
Components.utils.import("resource://gre/modules/Services.jsm");

const nsIAppShellService    = Components.interfaces.nsIAppShellService;
const nsISupports           = Components.interfaces.nsISupports;
const nsICategoryManager    = Components.interfaces.nsICategoryManager;
const nsIComponentRegistrar = Components.interfaces.nsIComponentRegistrar;
const nsICommandLine        = Components.interfaces.nsICommandLine;
const nsICommandLineHandler = Components.interfaces.nsICommandLineHandler;
const nsIFactory            = Components.interfaces.nsIFactory;
const nsIModule             = Components.interfaces.nsIModule;
const nsIWindowWatcher      = Components.interfaces.nsIWindowWatcher;

// chrome URI of your extension or application
const CHROME_URI = "chrome://jsbridge/content/";

// the contract id, CID, and category to be unique to your application.
const clh_contractID = "@mozilla.org/commandlinehandler/general-startup;1?type=jsbridge";

// use uuidgen to generate a unique ID
const clh_CID = Components.ID("{2872d428-14f6-11de-ac86-001f5bd9235c}");

// category names are sorted alphabetically. Typical command-line handlers use a
// category that begins with the letter "m".
const clh_category = "jsbridge";

// function jsbridgeServerObserver(server) {
//     dump('in jsbridgeServerObserver(server) ctor\n');
//     this.server = server;
// }
// jsbridgeServerObserver.prototype = {
//     classDescription: "observes for program shutdown and stops the jsbridge socket server",
//     classID: Components.ID("{ab8164cb-9f14-4ccf-be5d-22a60d1ba30d}"),
//     contractID: "@mozilla.org/jsbridge-server-observer;1",
//     QueryInterface: XPCOMUtils.generateQI([Components.interfaces.nsIObserver]),
//     _xpcom_categories: [{category: "quit-application", entry: 'jsbridgeserverobserver'}],
//     observe: function(aSubject, aTopic, aData) {
//         dump('in observe\n');
//         this.server.stop();
//         Services.obs.removeObserver(this, "quit-application", false);
//     }
// }

function SillyFileLogger(filename) {
  this.filename = filename;
  this._file = Cc["@mozilla.org/file/local;1"].createInstance(Ci.nsILocalFile);
  this._file.initWithPath(this.filename);
  this._fostream = Cc["@mozilla.org/network/file-output-stream;1"]
      .createInstance(Ci.nsIFileOutputStream);
  // Create with PR_WRITE_ONLY(0x02), PR_CREATE_FILE(0x08), PR_APPEND(0x10)
  this._fostream.init(this._file, 0x02 | 0x08 | 0x10, 0664, 0);
}
SillyFileLogger.prototype = {
  write: function(msg) {
    if (this._fostream) {
      var msgn = msg + "\n";
      this._fostream.write(msgn, msgn.length);
    }
  },
  close: function() {
    if (this._fostream)
      this._fostream.close();
    this._fostream = null;
    this._file = null;
  }
}; 

/**
 * The XPCOM component that implements nsICommandLineHandler.
 * It is also an event observer to shutdown the (socket) server on shutdown.
 * It also implements nsIFactory to serve as its own singleton factory.
 */
function jsbridgeHandler() {
  this.logger = new SillyFileLogger('/home/jhammel/log.txt');
  this.port = 24242;
}
jsbridgeHandler.prototype = {
  classID: clh_CID,
  contractID: clh_contractID,
  classDescription: "jsbridgeHandler",
  _xpcom_categories: [{category: "profile-after-change", service: true},
                      {category: "command-line-handler", entry: clh_category}],
  QueryInterface: XPCOMUtils.generateQI([Components.interfaces.nsIObserver]),

  /* nsIObserver */

  observe : function(aSubject, aTopic, aData) {
        this.logger.write('---' + aTopic + '---');
        switch(aTopic) {
        case "profile-after-change":
            this.init();
            break;
            
        case "sessionstore-windows-restored":
            this.startServer();
            break;

        case "quit-application":
            this.uninit();
            break;
        }
    },

  /* nsICommandLineHandler */

  handle : function clh_handle(cmdLine)
  {
    self.logger.write('handling command line');
    var port = cmdLine.handleFlagWithParam("jsbridge", false);
    var server = {};
    try {
      // use NSPR sockets to get offline+localhost support - needs recent js-ctypes
      Components.utils.import('resource://jsbridge/modules/nspr-server.js', server);
    }
    catch(e) {
      dump("jsbridge can't use NSPR sockets, falling back to nsIServerSocket - " +
           "OFFLINE TESTS WILL FAIL\n");
      Components.utils.import('resource://jsbridge/modules/server.js', server);
    }
      port = parseInt(port) || 24242;
      //      server.startServer(port)
      //      Services.obs.addObserver(new jsbridgeServerObserver(server.startServer(port), "quit-application", false));
  },

  // follow the guidelines in nsICommandLineHandler.idl
  // specifically, flag descriptions should start at
  // character 24, and lines should be wrapped at
  // 72 characters with embedded newlines,
  // and finally, the string should end with a newline
  helpInfo : "  -jsbridge            Port to run jsbridge on.\n",

  /* nsIFactory */

  createInstance : function clh_CI(outer, iid)
  {
    if (outer != null)
      throw Components.results.NS_ERROR_NO_AGGREGATION;

    return this.QueryInterface(iid);
  },

  lockFactory : function clh_lock(lock)
  {
    /* no-op */
  },

  /* internal methods */

  startServer: function() {
        this.logger.write("i is in your box startine ur serverz " + this.port);

        server = {};
        // import the server
        try {
            // use NSPR sockets to get offline+localhost support - needs recent js-ctypes
            Components.utils.import('resource://jsbridge/modules/nspr-server.js', server);
        }
        catch(e) {
            dump("jsbridge can't use NSPR sockets, falling back to nsIServerSocket - " +
                 "OFFLINE TESTS WILL FAIL\n");
            Components.utils.import('resource://jsbridge/modules/server.js', server);
        }
        
        // start the server
        this.server = server.startServer(this.port);
  },
  
  init: function() {
        this.logger.write("I'm observing this init function");
        Services.obs.addObserver(this, "quit-application", false);
        Services.obs.addObserver(this, "sessionstore-windows-restored", false);
    },

  uninit: function() {
        this.logger.write("I'm not observing this anymore");
        Services.obs.removeObserver(this, "quit-application", false);
        Services.obs.removeObserver(this, "sessionstore-windows-restored", false);
        this.server.stop();
        this.logger.write("We're done with this one");
    }
};

/**
 * XPCOMUtils.generateNSGetFactory was introduced in Mozilla 2 (Firefox 4).
 * XPCOMUtils.generateNSGetModule is for Mozilla 1.9.1 (Firefox 3.5).
 */
if (XPCOMUtils.generateNSGetFactory)
  const NSGetFactory = XPCOMUtils.generateNSGetFactory([jsbridgeHandler]);
else
  const NSGetModule = XPCOMUtils.generateNSGetModule([jsbridgeHandler]);
