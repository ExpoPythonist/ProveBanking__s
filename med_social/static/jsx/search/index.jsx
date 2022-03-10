var React = require('react'),
    Reflux = require('reflux'),
    classNames = require('classnames'),

    utils = require('../libs/utils.jsx'),
    ReactSelectize = require('../libs/react-selectize.jsx');


var Search = React.createClass({
  onResultSelected: function(value, $item){
    window.location.href = $item.attr('data-url');
  },

  render: function(){
    var name = 'Search';
    var renderItem = function(data, escape){
      return '<div data-url="' + data.url + '"><b>' + data.title + '</b> <span class="text-muted">in</span> <span class="text-primary">' + data.label + '</span></div>';
    }

    var persistentOptions = [
        {group: 'search', title: '[title]', label: 'suppliers', order: 100, value: 'vendors-link', type: 'SearchLink', url: '/vendors/?search=[title]'},
        {group: 'search', title: '[title]', label: 'people', order: 102, value: 'users-link', type: 'SearchLink', url: '/users/?search=[title]'},
      ];
      if (vetted.config.features.projects === true) {
        persistentOptions.unshift({title: '[title]', label: 'projects', order: 101, value: 'projects-link', type: 'SearchLink', url: '/projects/?search=[title]'});
      }
    var options = {
      key: name,
      onSelectizeChange: this.onChange,
      ref: name + '_selectize',
      valueField: "value",
      labelField: "label",
      searchField: "title",
      optgroups: [{value: "results", label: "Results found"}, {value: 'search', label: 'Search'}],
      optgroupField: 'group',
      selectId: "filter-" + name,
      placeholder: utils.getParamValueFromQueryString(window.location.search, 'search') || 'Search',
      name: name,
      remoteUrl: '/api/search/',
      onItemAdd: this.onResultSelected,
      sortField: 'order',
      persist: false,
      persistentOptions: persistentOptions,
      score: function(search) {
        var score = this.getScoreFunction(search);
          return function(item) {
            var s = score(item);
            if (item.type === 'SearchLink') {
              return 0.01;
            } else {
              return s;
            }
          };
      },
      preload: true,
      render: {
        option: renderItem,
        item: renderItem
      }
    };
    return <ReactSelectize {...options}/>;
  }
});

document.addEventListener('DOMContentLoaded', function() {
  var root = document.getElementById('global-search');
  if (root !== null) {
    var search = React.createFactory(Search)();
    React.render(search, root);
  };
}, false);
