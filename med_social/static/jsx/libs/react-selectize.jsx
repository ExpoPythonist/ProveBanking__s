
var React = require('react');

/* React selectize wrapper */
module.exports = React.createClass({
  getDefaultProps: function () {
    return {
      valueField: "id",
      labelField: "name",
      searchField: "name",
//sortField: ["order", "asc"],
      sort: {
        field: 'order',
        direction: 'asc'
      },
      create: false,
      remoteUrl: null,
      hideLabel: false,
      persistentOptions: [],
      items: [],
      plugins: []
    };
  },

  isMultiple: function (props) {
    // Selectize becomes 'multiple' when 'maxItems' is passed via settings
    return props.multiple || props.maxItems != undefined;
  },

  buildOptions: function () {
    var that = this;
    var o = {};

    o.plugins = this.props.plugins;
    o.valueField = this.props.valueField;
    o.labelField = this.props.labelField;
    o.searchField = this.props.searchField;
    o.sortField = this.props.sortField;
    o.persist = this.props.persist;
    o.render = this.props.render || {};
    if (this.props.optgroupField) {
      o.optgroupField = this.props.optgroupField;
    }

    if (this.props.optgroups) {
      o.optgroups = this.props.optgroups;
    }

    if (this.props.score) {
      o.score = this.props.score;
    }
    if (this.isMultiple(this.props)){
      o.maxItems = this.props.maxItems || null;
    }
    if (this.props.onItemAdd) {
      o.onItemAdd = this.props.onItemAdd;
    }
    o.options = this.props.items;
    o.create = this.props.create;

    window.SS = this;

    if (this.props.remoteUrl !== null) {
      o.load = function(query, callback) {
          $.ajax({
              url: that.props.remoteUrl,
              type: 'GET',
              dataType: 'json',
              data: {
                  q: query,
                  page_limit: 10,
              },
              error: function() {
                callback();
              },
              success: function(res) {
                var options = [];
                var selectize = that.getSelectizeControl();
                _.each(that.props.persistentOptions, function(o){
                  var opt = _.cloneDeep(o);
                  opt.title = opt.title.replace('[title]', query);
                  opt.url = opt.url.replace('[title]', query);
                  options.push(opt);
                  selectize.removeOption(opt.value);
                });
                callback(res.results.concat(options));
              }
          });
      };
      o.preload = this.props.preload || false;
    }
    return o;
  },

  getSelectizeControl: function () {
    var selectId = "#" + this.props.selectId,
      $select = $(selectId),
      selectControl = $select[0] && $select[0].selectize;

    return selectControl;
  },

  handleChange: function (val) {
    // IF Selectize is not multiple
    if(!this.isMultiple(this.props)){
      // THEN blur it before calling onSelectizeChange to prevent dropdown reopening
      this.getSelectizeControl().blur();
    }

    if(this.props.onSelectizeChange){
      this.props.onSelectizeChange(val, this);
    }
  },

  removeItem: function(value){
    this.getSelectizeControl().removeItem(value);
  },

  getValue: function(){
    return this.getSelectizeControl().getValue();
  },

  getItems: function(){
    return this.getSelectizeControl().options;
  },

  getItem: function(key){
    return this.getSelectizeControl().getItem(key);
  },

  rebuildSelectize: function () {
    var $select = null,
      selectControl = this.getSelectizeControl(),
      items = this.props.items || [];

    if(selectControl) {
      // rebuild
      selectControl.off();
      selectControl.clearOptions();
      if (items) {
        selectControl.load(function (cb) {cb(items)});
      }
    } else {
      // build new
      $select = $("#" + this.props.selectId).selectize(this.buildOptions());
      selectControl = $select[0].selectize;
    }

    selectControl.setValue(this.props.selectedValue);

    if(this.props.onSelectizeChange){
      selectControl.on('change', this.handleChange);
    }
  },

  componentDidMount: function () {
    this.rebuildSelectize();
  },

  componentDidUpdate: function () {
    this.rebuildSelectize();
  },

  render: function () {
    var classes = this.props.classes;
    if (this.props.label) {
      var label = <label for={this.props.selectId}>{this.props.label}</label>;
    } else {
      var label = '';
    }
    return <div className={classes && classes.length > 0 ? classes.join(' ') : ''}>
      {label}
      <select id={this.props.selectId} placeholder={this.props.placeholder} name={this.props.name}></select>
    </div>
  }
});
