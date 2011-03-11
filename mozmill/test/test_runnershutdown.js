var setupModule = function(module) {
    module.controller = mozmill.getBrowserController();
};

var testRunnerRestart = function() {
    controller.restartApplication('testUserRestart');
};

var testUserRestart = function() {
    controller.startUserShutdown(4000, true, 'testFinal');
  controller.click(new elementslib.Elem(controller.menus["file-menu"].menu_FileQuitItem));
};

var testFinal = function() {
    controller.stopApplication();
};