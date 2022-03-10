var Reflux = require('reflux'),
    React = require('react'),
    ProjectActions = require('./projects.jsx').Actions,
    Humanize = require('humanize-plus'),

    ReactSelectize = require('../libs/react-selectize.jsx'),
    Utils = require('../libs/utils.jsx');


var Actions = Reflux.createActions([
  ]);


var Store = Reflux.createStore({
  listenables: Actions,

  init: function(){
    this.filters = {};
  }
});


var Filters = React.createClass({
  statics: {
    filters: [
      {name: 'Group', url: '/api/divisions/', label: 'Group'},
      {name: 'Contact', url: '/api/users/', label: 'Point of contact'},
      {name: 'Role', url: '/api/roles/', label: 'Role'},
      {name: 'Location', url: '/api/locations/', label: 'Location'}

/*
      // Statuses defined at projects/mixins.py
      {name: 'Status', items: [
        {id: 1, name: 'Draft'},
        {id: 2, name: 'Staffing'},
        {id: 3, name:'Staffed'}
      ]},
*/
    ]
  },

  componentDidMount: function(){
    var $node = $(this.getDOMNode());
    $node.find('.dropdown-menu *').on('click', function(e){
      e.stopPropagation();
    });
  },

  componentWillUnmount: function(){
    var $node = $(this.getDOMNode());
    $node.find('.dropdown-menu *').off('click');
  },

  getInitialState: function(){
    return {};
  },

  onChange: function(value, selectize){
    ProjectActions.reload($(this.refs.form.getDOMNode()).serialize());

    var items = selectize.getItems();
    var selected = selectize.getValue();

    if (_.isArray(selected)) {
      selected = _.map(selected, function(val){
        return items[val];
      });
    } else {
      selected = [items[selected]];
    }
    var name = selectize.props.name;
    var state = {};
    state[name] = selected;
    this.setState(state);
  },

  render: function(){
    var that = this;
    var filters = Filters.filters.map(function(filter){
      var name = filter.name.toLowerCase();
      var options = {
        key: filter.name,
        onSelectizeChange: that.onChange,
        ref: name + '_selectize',
        valueField: "id",
        labelField: "name",
        searchField: "name",
        preload: true,
        selectId: "filter-" + filter.name,
        placeholder: filter.placeholder || filter.label,
        multiple: true,
        name: name,
        plugins: ['remove_button']
      };

      var selected = that.state[name];
      if (selected) {
        options.items = selected;
        options.selectedValue = _.map(selected, function(S){return S.id});
      }

      if (filter.url) {
        options.remoteUrl = filter.url;
      } else {
        options.items = filter.items;
      }

      return <div className="btn-group" key={"filter" + filter.name}>
        <button type="button" className="filter-btn btn btn-link no-underline dropdown-toggle" data-toggle="dropdown">
          {filter.label} <span className="caret"></span>
        </button>
        <ul className="dropdown-menu" role="menu">
          <li>
            <ReactSelectize {...options}/>
          </li>
        </ul>
      </div>
    });

    return <div className="filters nopadding">
      <div className="filter-row col-xs-12">
        <form ref="form" id="filter-form" className="form-inline" role="form">
          <div className="panel panel-default panel-filters">
            <div className="panel-body">
              {filters}
            </div>
          </div>
        </form>
      </div>
      <div>
        {_.map(this.state, function(selected, field){
          return <span>{_.map(selected, function(val){
            return <div className="btn-group btn-group-xs tag field-skills">
              <span className="btn btn-default btn-o disabled">{field.toLowerCase()}: {val.name}</span>
              <a onClick={function(){that.refs[field.toLowerCase() + '_selectize'].removeItem(val.id)}} className="btn-remove btn btn-default">
                <i className="fa fa-times"></i>
              </a>
            </div>
          })}</span>
        })}
        <br/>
        <br/>
      </div>
    </div>
  }
});


module.exports = {
  Filters: Filters
}
