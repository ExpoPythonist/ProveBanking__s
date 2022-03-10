window._vttd = window._vttd || {};

var Config = JSON.parse($('#global-vars').text());

window._vttd.config = Config;

module.exports = {
  'Config': _vttd.config
};
