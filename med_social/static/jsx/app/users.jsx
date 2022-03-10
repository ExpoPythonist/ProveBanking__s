var Reflux = require('reflux'),
	RestClient = require('../common/rest-clients.jsx').Client;


var Actions = Reflux.createActions({
	"reload": {},
	"create": {children: ['completed', 'failed']}
});


Actions.create.listen(function(data){
  var that = this;
  RestClient.users.create(data)
    .done(function(user){ that.completed(user, data); })
    .fail(function(xhr, text, error){
      that.failed(data, xhr, text, error);
    });
});


var Store = Reflux.createStore({
  listenables: Actions,

  init: function(){
    this.data = {
      users: [],
    };
  },

  onReload: function(){
    var that = this;
    RestClient.users.read().done(function(response){
      that.data.users = response.results;
      that.trigger(that.data);
    });
  },

  onCreateCompleted: function(user) {
  	this.data.users.push(user);
  	this.trigger(this.data);
  },
});


module.exports = {
  'Actions': Actions,
  'Store': Store
};
