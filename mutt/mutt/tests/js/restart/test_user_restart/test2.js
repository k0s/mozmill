var setupModule = function(module) {
  module.controller = mozmill.getBrowserController();
}

/**
 * This test should pass
 */
var testShutdownBeforeTimeout = function() {
    //  controller.startUserShutdown(100000, false);

    var foo = controller.mainMenu;

    //controller.click(new elementslib.Elem(controller.menus["file-menu"].menu_FileQuitItem));
    //ERROR | Test Failure: {"exception": {"stack": "()@resource://mozmill/modules/controller.js:406\n()@resource://mozmill/modules/frame.js -> file:///home/jhammel/mozmill/src/mozmill/mutt/mutt/tests/js/restart/test_user_restart/test2.js:10\n((function () {controller.click(new elementslib.Elem(controller.menus['file-menu'].menu_FileQuitItem));}))@resource://mozmill/modules/frame.js:499\n([object Object])@resource://mozmill/modules/frame.js:553\n(\"/home/jhammel/mozmill/src/mozmill/mutt/mutt/tests/js/restart/test_user_restart/test2.js\",null)@resource://mozmill/modules/frame.js:463\n(\"/home/jhammel/mozmill/src/mozmill/mutt/mutt/tests/js/restart/test_user_restart/test2.js\",false,null)@resource://mozmill/modules/frame.js:588\n((function (filename, invokedFromIDE, name) {var runner = new Runner(new Collector, invokedFromIDE);runner.runTestFile(filename, name);runner.end();return true;}),[object Proxy])@resource://jsbridge/modules/bridge.js:135\n(\"197e09d8-bc83-11e0-9d04-00262df16844\",(function (filename, invokedFromIDE, name) {var runner = new Runner(new Collector, invokedFromIDE);runner.runTestFile(filename, name);runner.end();return true;}),[object Proxy])@resource://jsbridge/modules/bridge.js:139\n", "message": "MenuTree is not defined", "fileName": "resource://mozmill/modules/controller.js", "name": "ReferenceError", "lineNumber": 406}}


    // controller.click(new elementslib.ID(controller.window.document, "new_FileQuitItem"));
    //ERROR | Test Failure: {"exception": {"stack": "createInstance(\"ID\",\"new_FileQuitItem\",null)@resource://mozmill/modules/mozelement.js:68\n([object XULDocument],\"new_FileQuitItem\")@resource://mozmill/modules/mozelement.js:80\n()@resource://mozmill/modules/frame.js -> file:///home/jhammel/mozmill/src/mozmill/mutt/mutt/tests/js/restart/test_user_restart/test2.js:15\n((function () {controller.click(new elementslib.ID(controller.window.document, \"new_FileQuitItem\"));}))@resource://mozmill/modules/frame.js:499\n([object Object])@resource://mozmill/modules/frame.js:553\n(\"/home/jhammel/mozmill/src/mozmill/mutt/mutt/tests/js/restart/test_user_restart/test2.js\",null)@resource://mozmill/modules/frame.js:463\n(\"/home/jhammel/mozmill/src/mozmill/mutt/mutt/tests/js/restart/test_user_restart/test2.js\",false,null)@resource://mozmill/modules/frame.js:588\n((function (filename, invokedFromIDE, name) {var runner = new Runner(new Collector, invokedFromIDE);runner.runTestFile(filename, name);runner.end();return true;}),[object Proxy])@resource://jsbridge/modules/bridge.js:135\n(\"b7ce8396-bc84-11e0-9a58-00262df16844\",(function (filename, invokedFromIDE, name) {var runner = new Runner(new Collector, invokedFromIDE);runner.runTestFile(filename, name);runner.end();return true;}),[object Proxy])@resource://jsbridge/modules/bridge.js:139\n", "message": "could not find element ID: new_FileQuitItem", "fileName": "resource://mozmill/modules/mozelement.js", "name": "Error", "lineNumber": 68}}



  //  controller.sleep(10000);
}
