var setupModule = function(module) {
    module.controller = mozmill.getBrowserController();
}

var testOne = function() {
    controller.restartApplication('testTwo');
}

var testTwo = function() {

}