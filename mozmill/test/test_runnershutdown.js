var setupModule = function(module) {
    module.controller = mozmill.getBrowserController();
};

var testRunnerRestart = function() {
    controller.restartApplication('testUserRestart');
};

var testUserRestart = function() {
    //    controller.startUserShutdown(
};

var testFinal = function() {
    controller.stopApplication();
};