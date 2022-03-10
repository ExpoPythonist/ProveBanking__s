var React = require('react');

module.exports = {
  'LoadingDots': React.createClass({
    render: function(){
      return <span className="loading-dots"><span>.</span><span>.</span><span>.</span></span>;
    }
  })
}
