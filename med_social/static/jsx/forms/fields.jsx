var React = require('react');


module.exports.Checkbox = React.createClass({
  componentDidMount: function(){
//new Switchery(this.refs.checkbox.getDOMNode(), {color: '#fd6107'});
  },

  onChange: function(){
    this.props.valueLink.requestChange($(this.refs.checkbox.getDOMNode()).is(':checked'));
  },
  render: function(){
    var props = {
      ref: "checkbox",
      type: "checkbox",
      name: this.props.name,
      onChange: this.onChange,
      defaultChecked: this.props.isChecked
    };

    return <div>
      <input {...props}/>
    </div>
  }
});

