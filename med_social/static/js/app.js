(function(){
  var inExec = function(){
    this.VERSION = 0.1;
    this.DOMAIN = 'proven.cc';
    this.$document = $(document);
    this.$window = $(window);
    this.$defaultContainer = null;
    this.baseClass = {
      initialize: function(){},
    };
    this.modules = {};
    this.classes = {};
    this.currentRoute = undefined;
    this.routes = {
      undefined: [],
    };
    this.__activeModules = [];
    this._pendingModules = [];
  };

  inExec.prototype.route = function(path){
    for (var route in this.routes) {
      if (this.routes.hasOwnProperty(route) &&
          path.match(new RegExp(route)) != null) {
        this.__realRoute(path, route);
      }
    }
    this.updateRouterState(path);
    this.currentRoute = path;
  };

  inExec.prototype.__realRoute = function(path, route){
    var previousRoute = this.currentRoute;
    $.event.trigger({
      type: 'app:preRoute',
      currentRoute: this.currentRoute,
      nextRoute: route,
      path: path
    });
    var modules = this.routes[route];
    if (modules === undefined) {
      return;
    }
    for (var i=0; i<modules.length; i++) {
      var module = modules[i];
      if (_.indexOf(this.__activeModules, module.name) == -1) {
        module.initialize(this.$defaultContainer);
        this.__activeModules.push(module.name);
      } else {
        if (module.update != undefined) {
          module.update();
        }
      }
    }
    $.event.trigger({
      type: 'app:postRoute',
      previousRoute: previousRoute,
      currentRoute: route,
      path: path
    });
  },

  inExec.prototype.updateRouterState = function(path){
    this.__activeModules = _.uniq(this.__activeModules);
    var toDestroy = [];

    for (var i=0; i < this.__activeModules.length; i++) {
      var module = this.modules[this.__activeModules[i]];
      var destroy = true;
      for (var j=0; j < module.regexRoutes.length; j++) {
        var regexRoute = module.regexRoutes[j];
        if (path.match(regexRoute) !== null) {
          destroy = false;
          break;
        }
      }
      if (destroy == true) {
        toDestroy.push(module.name);
      }
    }

    for (var i=0; i < toDestroy.length; i++) {
      var name = toDestroy[i];
      var module = this.modules[name];
      if (module.destroy != undefined) {
        module.destroy();
      }
      this.__activeModules = _.without(this.__activeModules, name);
    }
  },

  inExec.prototype.initialize = function($container){
    var that = this;
    this.$defaultContainer = $container || $('body');
    this._pendingModules.reverse();
    var module = this._pendingModules.pop();
    this.currentRoute = window.location.pathname;
    while (module != undefined) {
      var realModule = module.module;
      this.modules[module.name] = realModule;
      var routes = realModule.routes;
      realModule.regexRoutes = [];
      if (realModule.routes != undefined) {
        _.each(realModule.routes, function(route){
          var regexRoute = new RegExp(route);
          realModule.regexRoutes.push(regexRoute);
          that.routes[route] = that.routes[route] || [];
          that.routes[route].push(realModule);
          if (that.currentRoute.match(regexRoute) != null) {
            realModule.initialize(that.$defaultContainer);
            that.__activeModules.push(module.name);
          }
        })
      } else {
        realModule.initialize(this.$defaultContainer);
      }
      var module = this._pendingModules.pop();
      this.updateRouterState(this.currentRoute);
    }
  };

  inExec.prototype.register = function(module){
    this._pendingModules.push({name:module.name, module: module});
  };

  inExec.prototype.extendClass = function(module){
    var tempObj = {};
    _.extend(tempObj, this.baseClass, module);
    var newClass = function(options){this.initialize(options)};
    newClass.prototype = tempObj;
    this.classes[module.name] = newClass;
  };

  window._inExec = new inExec();
  $(document).ready(function(){
    _inExec.initialize();

    $(document).ajaxComplete(function(e, xhr, settings) {
      if (xhr.getResponseHeader('HTTP_X_PJAX') === 'true') {
        return;
      }

      if (xhr.status == 278) {
        var newLocation = '';
        var $body = $('body');
        var key = 'next';
        var value = window.location.pathname;
        var uri = xhr.getResponseHeader("Location");
        var re = new RegExp("([?&])" + key + "=.*?(&|$)", "i");
        var separator = uri.indexOf('?') !== -1 ? "&" : "?";
        if (uri.match(re)) {
          newLocation = uri.replace(re, '$1' + key + "=" + value + '$2');
        }
        else {
          newLocation = uri + separator + key + "=" + value;
        }

        $body.addClass('text-center');
        $body.html('<h1>redirecting...</h1><a href="'+newLocation+'" class="text-underline">click here</a> if you are not redirected automatically.');
        window.location.href = newLocation
      }
    });
    window.dispatchEvent(new Event('inExec:initialized'));
//    FastClick.attach(document.body);
  });
})();
