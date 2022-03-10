var CSRF = require('../common/csrf.jsx').CSRFManager;

var vetted = new function(){
  this.routers = {};
}();

window._vttd = vetted;

module.exports = {
  'vetted': vetted
};
