var React = require('react');


var Star = React.createClass({
  render: function(){
    return <i className={"fa fa-star " + (this.props.active === true ? 'active': '')}></i>;
  }
});


var Stars = React.createClass({
  render: function(){
    stars = [];
    for (var i=0; i < this.props.limit; i++) {
      stars.push(<Star key={i} active={i < Math.round(this.props.score)}/>);
    }

    if (this.props.score > 0 && this.props.score < 1.5) {
      var color = "one";
    }
    else if  (this.props.score > 1.5 && this.props.score < 2.5) {
      var color = "two";
    }
    else if  (this.props.score > 2.5 && this.props.score < 3.5) {
      var color = "three";
    }
    else if  (this.props.score > 3.5 && this.props.score < 4.5) {
      var color = "four";
    }
    else  if (this.props.score > 4.5 && this.props.score <= 5) {
      var color = "five";
    }
    else {
      var color = "secondary"
    }

    return <div className={"rating-stars star_" +color }  title={"Average review score: " + this.props.score}>{stars}</div>
  }
});


module.exports = {
  'Stars': Stars,
  'Star': Star
};
