var React = require('react');

var Trigger = React.createClass({
  render: function(){
    return <div data-drop-role="trigger">{this.props.children}</div>
  }
});


var Content = React.createClass({
  render: function(){
    var classes = this.props.className ? this.props.className : '';
    return <div data-drop-role="content" className={classes}>{this.props.children}</div>
  }
});


var Item = React.createClass({
  onClick: function(event, extra){
    if (this.props.onClick) {
      this.props.onClick(event, extra);
    }
  },
  render: function(){
    var classes = this.props.className ? this.props.className : '';
    return <div data-drop-role="item" onClick={this.onClick} className={"drop-item " + classes}>{this.props.children}</div>
  }
});


var Drop = React.createClass({
  componentDidMount: function(){
    var content = _.find(this.props.children, function(child){
      return child.type.displayName === 'Content';
    });
    this.drop = new window.Drop({
      classes: 'drop-theme-basic drop-hero',
      target: this.getDOMNode().querySelector('[data-drop-role=trigger]'),
      content: React.renderToStaticMarkup(content),
      position: this.props.position || 'bottom right',
      openOn: 'click'
    });
    React.render(content, this.drop.content.children[0]);
    this.drop.position();
  },

  componentWillUnmount: function(){
    this.drop.destroy();
  },

  close: function(){
    this.drop.close();
  },

  open: function(){
    this.drop.open();
  },

  render: function(){
    var classes = 'anchor';
    var trigger = _.find(this.props.children, function(child){
      return child.type.displayName === 'Trigger';
    });
    return <div className={'anchor ' + this.props.className}>{trigger}</div>
  }
});


module.exports = {
  'Drop': Drop,
  'Trigger': Trigger,
  'Content': Content,
  'Item': Item
};
