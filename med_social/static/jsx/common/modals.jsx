var React = require('react'),
    classNames = require('classnames');

var Modal = React.createClass({
  sizes: {
    'large': 'modal-lg',
    'regular': '',
    'small': 'modal-sm'
  },

  getDefaultProps: function(){
    return {size: 'regular'};
  },

  componentDidMount: function(){
    this.$modal = $(this.getDOMNode());
    this.$modal.on('hidden.bs.modal', this.onModalClosed);
    if (this.props.show === true) {
      $(this.getDOMNode()).modal('show');
    }
  },

  componentDidUpdate: function(){
    if (this.props.show === true) {
      $(this.getDOMNode()).modal('show');
    }
  },

  componentWillUnmount: function() {
    this.$modal.off('hidden.bs.modal');
  },

  onModalClosed: function(){
    if (this.props.onModalClosed) {
      this.props.onModalClosed();
    }
  },

  hide: function(){
    this.$modal.modal('hide');
  },

  render: function(){
    if (_.isArray(this.props.children)) {
      var children = this.props.children;
    } else {
      var children = [this.props.children];
    }

    var header = _.find(children, function(child){
      return child.props.modalRole === "header";
    });

    var body = _.find(children, function(child){
      return child.props.modalRole === "body";
    });

    var footer = _.find(children, function(child){
      return child.props.modalRole === "footer";
    });

    return <div className="modal fade" data-keyboard={false} data-backdrop="static">
      <div className={"modal-dialog " + this.sizes[this.props.size]}>
        <div className="modal-content">
          {header}
          {body}
          {footer}
        </div>
      </div>
    </div>
  }
});


var Body = React.createClass({
  getDefaultProps: function(){
    return {modalRole: "body"};
  },

  render: function(){
    var style = {'padding': '5px 10px'};
    _.extend(style, this.props.style || {});
    var klass = classNames({'modal-body': true});
    return <div className={klass} style={style}>{this.props.children}</div>;
  }
});


var Footer = React.createClass({
  getDefaultProps: function(){
    return {modalRole: "footer"};
  },

  render: function(){
    var classes = "modal-footer ";
    if (this.props.className) {
      classes += this.props.className;
    }
    return <div className={classes}>{this.props.children}</div>;
  }
})


var Header = React.createClass({
  getDefaultProps: function(){
    return {modalRole: "header"};
  },

  render: function(){
    var style = {'padding': '5px 10px'};
    _.extend(style, this.props.style || {});
    return <div className="modal-header" style={style}>{this.props.children}</div>;
  }
})


module.exports = {
  'Modal': Modal,
  'Body': Body,
  'Footer': Footer,
  'Header': Header
}
