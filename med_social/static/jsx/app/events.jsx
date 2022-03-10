var vetted = require('../common/vetted.jsx').vetted;

var Events = function(){
  this.$eventBus = $({});
};

Events.prototype.on = function(eventName, callback) {
  this.$eventBus.on(eventName, callback);
};

Events.prototype.off = function(eventName, callback) {
  if (callback === undefined) {
    this.$eventBus.off(eventName, callback);
  } else {
    this.$eventBus.off(eventName);
  }
};

Events.prototype.trigger = function(eventName, context) {
  this.$eventBus.trigger(eventName, context);
};

vetted.Events = new Events();

module.exports = {
  'Events': vetted.Events
};
