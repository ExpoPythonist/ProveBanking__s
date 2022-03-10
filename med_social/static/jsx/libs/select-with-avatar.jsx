var React = require('react'),
    Select = require('react-select');

var AVATAR_SIZE = 15;

var AvatarOption = React.createClass({

  handleMouseDown: function(event) {
    event.preventDefault();
    event.stopPropagation();
    this.props.onSelect(this.props.option, event);
  },
  handleMouseEnter: function(event) {
    this.props.onFocus(this.props.option, event);
  },
  handleMouseMove: function(event){
    if (this.props.focused) return;
    this.props.onFocus(this.props.option, event);
  },
  handleMouseLeave: function (event) {
    this.props.onUnfocus(this.props.option, event);
  },
  render: function () {
    return (
      <div className={this.props.className}
        onMouseDown={this.handleMouseDown}
        onMouseEnter={this.handleMouseEnter}
        onMouseMove={this.handleMouseMove}
        onMouseLeave={this.handleMouseLeave}
        title={this.props.option.title}>

        <div  className="media">
          <img src={this.props.option.logo}  className="select-img pull-left media-left" />
          <div className="media-body">
            <div className="">{this.props.children}</div>
            <div className="small text-muted">{this.props.option.website}</div>
          </div>
        </div>
      </div>
    );
  }
});

var AvatarValue = React.createClass({

  render: function() {

    return (
      <div className="Select-value" title={this.props.value.title}>
        <span className="Select-value-label">
          {this.props.children}
        </span>
      </div>
    );
  }
});

// const UsersField = React.createClass({
//   propTypes: {
//     hint: React.PropTypes.string,
//     label: React.PropTypes.string,
//   },
//   getInitialState () {
//     return {};
//   },
//   setValue (value) {
//     this.setState({ value });
//   },
//   render () {
//     return (
//       <div className="section">
//         <h3 className="section-heading">{this.props.label}</h3>
//         <Select
//           onChange={this.setValue}
//           optionComponent={GravatarOption}
//           options={USERS}
//           placeholder="Select user"
//           value={this.state.value}
//           valueComponent={GravatarValue}
//           />
//         <div className="hint">This example implements custom Option and Value components to render a Gravatar image for each user based on their email</div>
//       </div>
//     );
//   }
// });

module.exports = {
  AvatarValue: AvatarValue,
  AvatarOption: AvatarOption,
}
