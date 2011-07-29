var setupModule = function(module) {
  module.controller = mozmill.getBrowserController();
}

/**
 * This test should pass
 */
var testShutdownBeforeTimeout = function() {
  controller.startUserShutdown(100000, false);
  //  controller.click(new elementslib.Elem(controller.menus["file-menu"].menu_FileQuitItem));
  controller.click(new elementslib.ID(controller.window.document, "new_FileQuitItem"));
  controller.sleep(10000);
}
