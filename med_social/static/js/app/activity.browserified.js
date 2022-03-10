(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
_inExec.register({
  name: 'activity',
  routes: [''],
  initialize: function(){
    this.update();
  },
  update: function(){
    this.destroy();
    this.setup();
  },
  destroy: function(){
  },
  setup: function(){
    $( ".unread-event" ).each(function( index ) {
      var eventUrl = $(this).attr('data-unread-event-url');
      if (eventUrl){
        $.post(eventUrl);
      }
    });
  }
});
},{}]},{},[1])
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIi4uLy4uLy4uLy4uL25vZGVfbW9kdWxlcy9icm93c2VyaWZ5L25vZGVfbW9kdWxlcy9icm93c2VyLXBhY2svX3ByZWx1ZGUuanMiLCJhY3Rpdml0eS5qcyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQTtBQ0FBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQSIsImZpbGUiOiJnZW5lcmF0ZWQuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlc0NvbnRlbnQiOlsiKGZ1bmN0aW9uIGUodCxuLHIpe2Z1bmN0aW9uIHMobyx1KXtpZighbltvXSl7aWYoIXRbb10pe3ZhciBhPXR5cGVvZiByZXF1aXJlPT1cImZ1bmN0aW9uXCImJnJlcXVpcmU7aWYoIXUmJmEpcmV0dXJuIGEobywhMCk7aWYoaSlyZXR1cm4gaShvLCEwKTt2YXIgZj1uZXcgRXJyb3IoXCJDYW5ub3QgZmluZCBtb2R1bGUgJ1wiK28rXCInXCIpO3Rocm93IGYuY29kZT1cIk1PRFVMRV9OT1RfRk9VTkRcIixmfXZhciBsPW5bb109e2V4cG9ydHM6e319O3Rbb11bMF0uY2FsbChsLmV4cG9ydHMsZnVuY3Rpb24oZSl7dmFyIG49dFtvXVsxXVtlXTtyZXR1cm4gcyhuP246ZSl9LGwsbC5leHBvcnRzLGUsdCxuLHIpfXJldHVybiBuW29dLmV4cG9ydHN9dmFyIGk9dHlwZW9mIHJlcXVpcmU9PVwiZnVuY3Rpb25cIiYmcmVxdWlyZTtmb3IodmFyIG89MDtvPHIubGVuZ3RoO28rKylzKHJbb10pO3JldHVybiBzfSkiLCJfaW5FeGVjLnJlZ2lzdGVyKHtcbiAgbmFtZTogJ2FjdGl2aXR5JyxcbiAgcm91dGVzOiBbJyddLFxuICBpbml0aWFsaXplOiBmdW5jdGlvbigpe1xuICAgIHRoaXMudXBkYXRlKCk7XG4gIH0sXG4gIHVwZGF0ZTogZnVuY3Rpb24oKXtcbiAgICB0aGlzLmRlc3Ryb3koKTtcbiAgICB0aGlzLnNldHVwKCk7XG4gIH0sXG4gIGRlc3Ryb3k6IGZ1bmN0aW9uKCl7XG4gIH0sXG4gIHNldHVwOiBmdW5jdGlvbigpe1xuICAgICQoIFwiLnVucmVhZC1ldmVudFwiICkuZWFjaChmdW5jdGlvbiggaW5kZXggKSB7XG4gICAgICB2YXIgZXZlbnRVcmwgPSAkKHRoaXMpLmF0dHIoJ2RhdGEtdW5yZWFkLWV2ZW50LXVybCcpO1xuICAgICAgaWYgKGV2ZW50VXJsKXtcbiAgICAgICAgJC5wb3N0KGV2ZW50VXJsKTtcbiAgICAgIH1cbiAgICB9KTtcbiAgfVxufSk7Il19
