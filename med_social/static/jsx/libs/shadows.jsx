var React = require('react');

var Shadow = React.createClass({
  render: function(){
    return <div className="shadows">
      <div className="shadow-bottom"></div>
      <div className="shadow-top"></div>
    </div>
  }
});

module.exports = {
  'Shadow': Shadow,
};
