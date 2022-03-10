var React = require('react/addons'),
    Reflux = require('reflux'),
    ReactCSSTransitionGroup = React.addons.CSSTransitionGroup,
    Select = require('react-select'),
    ClassNames = require('classnames'),
    Modal = require('../common/modals.jsx').Modal,
    ModalBody = require('../common/modals.jsx').Body,
    ModalFooter = require('../common/modals.jsx').Footer,
    ModalHeader = require('../common/modals.jsx').Header,

    LoadingDots = require('../common/loading-dots.jsx').LoadingDots,
    RestClient = require('../common/rest-clients.jsx').Client,
    Notifications = require('../common/notifications.jsx').Actions,
    Events = require('../app/events.jsx').Events,
    Config = require('../common/config.jsx').Config,
    Utils = require('../libs/utils.jsx');
    RFP = require('../rfps/actions_and_stores.jsx'),
    vetted = require('../common/vetted.jsx').vetted;

var Actions = Reflux.createActions([
    "reload",
    "toggleCart",
    "showCart",
    "hideCart",
    "showIfReady",

    "addPerson",
    "addVendor",
    "addRequest",
    "addRFP",
    "removePerson",
    "removeVendor",
    "removeRequest",
    "removeRFP",

    "setPersonStatus",
    "checkout"
  ]);


var CartStore = Reflux.createStore({
  listenables: Actions,

  init: function(){
    this.client = RestClient.cart;
    this.data = {
      cart: null,
      isLoading: false,
      isOpen: false // false for prod
    };
  },

  onCheckout: function(cart_id){
    var that = this;
    if (!this.data.cart.request) {
      window.location.pathname = '/checkout/';
    }
    var oldRequest = this.data.cart.request;
    this.data.isLoading = true;
    this.trigger(this.data);
    this.client.checkout(cart_id)
      .done(function(cart){
        that.data.isLoading = false;
        that.setCart(cart);
        Notifications.new({message: "Added people and suppliers to the project. Redirecting now.", type: "success"});
        window.location.pathname = '/projects/' + oldRequest.project.id;
      })
      .fail(function(response){
        that.data.isLoading = false;
        that.trigger(that.data);
        _.each(response.responseJSON, function(error){
          Notifications.new({message: error, type: "error"});
        });
      });
  },

  onReload: function(queryString){
    var that = this;
    this.client.read().done(function(result){
      that.setCart(result);
    });
  },

  setCart: function(cart){
    cart.count = (cart.people ? cart.people.length : 0) + (cart.vendors ? cart.vendors.length : 0);
    this.data.cart = cart;
    this.trigger(this.data);
    // must emit signal asynchronously or any exception in callbacks will
    // break the data flow in this module.
    setTimeout(function(){
      Events.trigger('cart:changed', cart);
    }, 0);
  },

  onToggleCart: function(){
    if (this.data.isOpen === true) {
      this.onHideCart();
    } else {
      this.onShowCart();
    }
  },

  onShowCart: function(refresh){
    if (refresh === undefined) {
      refresh = true;
    }
    this.data.isOpen = true;
    this.trigger(this.data);
    if ((this.data.isOpen === true) && refresh) {
      Actions.reload();
    }
  },

  onShowIfReady: function(){
    if (this.data.cart && this.data.cart.request) {
      this.data.isOpen = true;
      this.trigger(this.data);
    }
  },

  onHideCart: function(){
    this.data.isOpen = false;
    this.trigger(this.data);
    if (this.data.isOpen === true) {
      Actions.reload();
    }
  },

  _addPerson: function(person, force) {
    force = force || true;
    var existing = _.findWhere(this.data.cart.people, {id: person.id});
    if (existing === undefined) {
      this.data.cart.people.unshift(person);
      this.setCart(this.data.cart);
    } else if (force === true) {
      _.extend(_.findWhere(this.data.cart.people, {id: person.id}), person);
      this.setCart(this.data.cart);
    }
  },

  _removePerson: function(person, force) {
    var cart = this.data.cart;
    cart.people = _.filter(cart.people, function(P){return P.id !== person.id});
    this.setCart(cart);
  },

  _removeVendor: function(vendor, force) {
    var cart = this.data.cart;
    cart.vendors = _.filter(cart.vendors, function(P){return P.id !== vendor.id});
    this.setCart(cart);
  },

  _addVendor: function(vendor, force){
    force = force || true;
    var existing = _.findWhere(this.data.cart.vendors, {id: vendor.id});
    if (existing === undefined) {
      this.data.cart.vendors.unshift(vendor);
      this.setCart(this.data.cart);
    } else if (force === true) {
      this.data.cart.vendors[_.indexOf(this.data.cart.vendors, existing)] = _.extend(existing, vendor);
      this.setCart(this.data.cart);
    }
  },

  _addRequest: function(request, force){
    force = force || true;
    this.data.cart.request = request;
    this.setCart(this.data.cart);
  },

  onAddPerson: function(person) {
    var that = this;
    this._addPerson(person);
    this.client.add_person(this.data.cart.id, {id: person.id})
      .done(function(data){
        var cart = that.data.cart;
        if (_.findWhere(cart.people, {id: person.id}) !== undefined) {
          cart.people = _.filter(cart.people, function(P){return P.id !== person.id});
        }
        cart.people.unshift(data);
        that.setCart(cart);
      })
      .fail(function(){
        Notifications.new({message: "Failed to shortlist person. Please try again.", type: "error"});
        that._removePerson(person);
        that.trigger(that.data);
      });
  },

  onAddVendor: function(vendor){
    var that = this;
    this.client.add_vendor(this.data.cart.id, {id: vendor.id})
    .done(function(data){
      var cart = that.data.cart;
      if (_.findWhere(cart.vendors, {id: vendor.id}) !== undefined) {
        cart.vendors = _.filter(cart.vendors, function(P){return P.id !== vendor.id});
      }
      cart.vendors = cart.vendors || [];
      cart.vendors.unshift(data);
      that.setCart(cart);
    });
  },

  onAddRequest: function(request){
    var that = this;
    var cart = that.data.cart;
    var oldRequest = cart.request;
    cart.request = request;
    this.data.isLoading = true;
    this.setCart(cart);
    Actions.showCart(false);
    this.client.add_request(this.data.cart.id, {id: request.id})
      .done(function(data){
        that.setCart(data);
      })
      .fail(function(){
        Notifications.new({message: "Failed to select request. Please try again.", type: "error"});
        cart.request = oldRequest;
        that.setCart(cart);
      })
      .always(function(){
        that.data.isLoading = false;
        that.trigger(that.data);
      });
  },

  onAddRFP: function(rfp, force){
    var that = this;
    var cart = that.data.cart;
    var oldRfp = cart.rfp;
    cart.rfp = rfp;
    this.setCart(cart);
    Actions.showCart(false);
    this.client.add_rfp(this.data.cart.id, {id: rfp.id})
      .done(function(data){
        that.setCart(data);
      })
      .fail(function(){
        Notifications.new({message: "Failed to select request. Please try again.", type: "error"});
        cart.rfp = oldRfp;
        that.setCart(cart);
      })
      .always(function(){
        that.data.isLoading = false;
        that.trigger(that.data);
      });
  },

  onRemovePerson: function(person) {
    var that = this;
    var cart = this.data.cart;
    var oldPerson = _.findWhere(cart.people, {id: person.id});
    this._removePerson(person);

    this.client.remove_person(cart.id, {id: person.id})
      .fail(function(){
        Notifications.new({message: "Error removing person from cart", type: "error"});
        that._addPerson(oldPerson);
    });
  },

  onRemoveVendor: function(vendor) {
    var that = this;
    var cart = this.data.cart;
    var oldVendors = _.findWhere(cart.vendors, {id: vendor.id});
    this._removeVendor(vendor);

    this.client.remove_vendor(this.data.cart.id, {id: vendor.id})
      .fail(function(){
        Notifications.new({message: "Error removing vendor from cart", type: "error"});
        that._addVendor(oldVendor);
    });
  },

  onRemoveRequest: function() {
    var that = this;
    var cart = this.data.cart;
    var oldRequest = cart.request;
    cart.request = null;
    this.setCart(cart);
    this.client.remove_request(this.data.cart.id)
      .fail(function(){
        cart.request = oldRequest;
        that.setCart(cart);
        Notifications.new({message: "Error removing request from cart", type: "error"});
    });
  },

  onRemoveRFP: function() {
    var that = this;
    var cart = this.data.cart;
    var oldRfp = cart.rfp;
    cart.rfp = null;
    this.setCart(cart);
    this.client.remove_rfp(this.data.cart.id)
      .fail(function(){
        cart.rfp = oldRfp;
        that.setCart(cart);
        Notifications.new({message: "Error removing Request from cart", type: "error"});
    });
  },

  onSetPersonStatus: function(person, _status){
    var that = this;
    var cart = this.data.cart;
    var oldStatus = _.findWhere(cart.people, {id: person.id}).status;
    _status = _.findWhere(person.status_options, {id: Number(_status)});
    _.findWhere(cart.people, {id: person.id}).status = _status;
    this.setCart(cart);

    this.client.set_person_status(this.data.cart.id, {person: person.id, status: _status.id})
      .done(function(person){
        that._addPerson(person, true);
      })
      .fail(function(){
        person.status = oldStatus;
        that._addPerson(person, true);
        Notifications.new({message: "Error changing status. Please try again.", type: "error"});
      });
  }
});


var Cart = React.createClass({
//listenables: Actions,

  mixins: [Reflux.connect(CartStore), Reflux.ListenerMixin,
           Reflux.listenTo(RFP.Actions.shareRFP.completed, "onRFPShareCompleted")],

  getInitialState: function(){
    return CartStore.data;
  },

  componentDidMount: function(){
    Actions.reload();
  },

  onRFPShareCompleted: function(){
    Actions.hideCart();
  },

  render: function(){
    if (this.state.cart === null) {
      return <div className="btn btn-xs btn-secondary-dark btn-o hidden">
        <i className="fa fa-ellipsis-h"></i>
      </div>;
    } else {
      var classes = ClassNames({
        'btn-request': true,
        //'btn-primary': this.state.cart.count !== 0,
        //'btn-secondary-dark btn-o': this.state.cart.count === 0
      });

      return <div className={classes} onClick={Actions.toggleCart}>
        <div className="btn-floating btn-send-request cart-folder" data-toggle="tooltip" data-placement="top" title="send request">
          <span className="cart-count">{this.state.cart.count}</span>
        </div>
      </div>
    }
  }
});


var Person = React.createClass({
  mixins: [React.addons.LinkedStateMixin],

  onStatusChange: function(e, x){
    var status = Number(e.target.value);
    if (status !== this.props.status.id) {
      Actions.setPersonStatus(this.props, e.target.value);
    }
  },

  render: function() {
    var that = this;
    if (this.props.avatar) {
      var avatar = <img src={this.props.avatar} className="avatar"/>
    } else {
      var avatar = <div className="avatar">{this.props.initials}</div>
    }
    if (this.props.request && this.props.status_options) {
      var status = this.props.status ? this.props.status.id : '';
      var select = <select value={status} ref="status" onChange={this.onStatusChange}>
        {this.props.status_options.map(function(status){
          return <option value={status.id} key={status.id}>{status.value}</option>
        })}
      </select>
    }

    return <li className="list-group-item row" key={this.props.id + '-person'}>
      <div className="col-xs-10">
        <div className="media">
          <span className="pull-left media-left">
            {avatar}
          </span>
          <div className="media-body">
            <div className="media-heading">{this.props.name}</div>
            {select}
          </div>
        </div>
      </div>
      <div className="col-xs-2 text-right">
        <a href="#" onClick={function(){Actions.removePerson({id: that.props.id})}}>
          <i className="fa fa-trash text-muted"></i>
        </a>
      </div>
    </li>;
  }
});


var Vendor = React.createClass({
  render: function() {
    var that = this;
    return <li className="list-group-item row" key={this.props.id + '-vendor'}>
      <div className="col-xs-10">
        <div className="media">
          <span className="pull-left media-left">
            <div className="logo-container">
              <img className="img-responsive" src={this.props.logo} />
            </div>
          </span>
          <div className="media-body">
            <div className="media-heading">{this.props.name}</div>
          </div>
        </div>
      </div>
      <div className="col-xs-2 text-right">
        <a href="#" onClick={function(){Actions.removeVendor({id: that.props.id})}}>
          <i className="fa fa-trash text-muted" ></i>
        </a>
      </div>
    </li>;
  }
});


var CartList = React.createClass({
  render: function(){
    var that = this;
    if (_.isEmpty(this.props.cart.people) && _.isEmpty(this.props.cart.vendors)) {
      if (Config.features.projects === true){
        return <ul key="cart-items" className="list-group cart-items">
          <li className="list-group-item row">Try seaching for <a href="/users/">people</a> or <a href="/vendors/">suppliers</a> to shortlist.</li>
        </ul>
      } else {
        return <ul key="cart-items" className="list-group cart-items">
          <li className="list-group-item row">Try seaching for <a href="/vendors/">suppliers</a> to shortlist.</li>
        </ul>
      }
    } else {
      return <ul key="cart-items" className="list-group cart-items">
        {this.props.cart.people.map(function(person){
          return <Person {...person} key={'person-' + person.id} request={that.props.cart.request}/>
        })}

        {this.props.cart.vendors.map(function(vendor){
          return <Vendor {...vendor} key={"vendor-" + vendor.id}/>
        })}
      </ul>
    }
  }
});


var CartBody = React.createClass({
  mixins: [
    Reflux.connect(CartStore), Reflux.ListenerMixin,
    Reflux.listenTo(Actions.hideCart, "onHideCart")
  ],

  componentDidMount: function(){
    this.listenTo(RFP.Actions.createFromTemplate.completed, this.onRFPFromTemplate);
  },

  getInitialState: function(){
    return _.extend(CartStore.data, {isLoading: false});
  },

  onCheckout: function(){
    Actions.checkout(this.state.cart.id);
  },

  onRFPCheckout: function() {
    var control = this.refs.rfpSelect;
    var selected = control.state.value;
    var rfp = this.state.cart.rfp || this.state.selectedRFP;

    if ((rfp == undefined) || (rfp.id == undefined)) {
      rfp = _.findWhere(RFP.Store.data.requests, {id: Number(selected)});
    }

    if ((rfp !== undefined) && (rfp.id !== undefined)) {
      if (rfp.is_template){
        RFP.Actions.createFromTemplate(rfp);
      } else {
        RFP.Actions.shareRFP(rfp, this.state.cart.vendors);
      }
    }
  },

  onRFPSelect: function(rfp_id, values) {

    if (rfp_id && rfp_id != ""){
      var rfp = rfp_id;
      Actions.addRFP(rfp);
      this.setState({'selectedRFP': rfp_id});
    } else {
      Actions.removeRFP();
    }
  },

  onRFPFromTemplate: function(rfp) {
    if (this.state.isOpen){
      Notifications.new({id: "rfp-redirect-" + rfp.id, message: "Redirecting...", type: "success"});
      window.location.pathname = '/rfps/' + rfp.id + '/edit';
    }
  },

  onHideCart: function() {
    this.refs.modal.hide();
  },

  searchRFP: function(query, cb) {
    RestClient.rfps.read({}, {search: query, is_template: 'False'})
      .done(function(data){
        var result = {options: data.results}
        if (data.next === null) {
          result.complete = true;
        }
        cb(null, result);
      })
      .fail(function(xhr, reason, error){
        cb(error, {options: []});
      });
  },

  render: function(){
    var classes = ClassNames({
      'cart-body-right': true,
      'hidden': this.state.isOpen === false
    });

    if (this.state.cart === null) {
      return <div className={classes}>
        Loading...
      </div>
    } else {
      if (this.state.isLoading) {
        var loading = <div className="loading-overlay">
          Loading<LoadingDots/>
        </div>
      }

      if (this.state.cart.count !== 0) {
        if (Config.features.projects === true) {
          if (this.state.cart.request) {
            var cta = <button onClick={this.onCheckout} className="btn btn-primary">
                add to selected request <i className="fa fa-long-arrow-right"></i>
              </button>
          } else {
            var cta = <a href="/shortlist/" className="btn btn-primary">
              select a request <i className="fa fa-long-arrow-right"></i>
            </a>
          }
        } else if(this.state.cart.rfp){
          var cta = <button onClick={this.onRFPCheckout} className="btn btn-primary">
                {this.state.cart.rfp.is_template ? "compose" : "send" } request <i className="fa fa-long-arrow-right"></i>
              </button>
        }
        var actions = <div className="cart-actions col-xs-12 text-center">
          {cta}
        </div>
      }

      if (this.state.cart.request) {
        var _req = this.state.cart.request;
        if (_req.role && _req.role.color) {
          var roleStyle = {borderLeft: '10px solid' +_req.role.color};
        } else {
          var roleStyle = {};
        }
        var request = <div className="row">
          <div className="col-xs-12 list-header">
            Selected request
          </div>
          <div className="col-xs-12">
            <div className="selected-request row" style={roleStyle}>
              <div className="col-xs-10 nopadding">
                <div className="col-xs-12 nopadding text-ellipsis"><small>{_req.project.title}</small></div>
                <b>{_req.title}</b>
              </div>
              <div className="col-xs-2 text-right nopadding">
                <a href="#" onClick={function(){Actions.removeRequest()}}>
                  <i className="fa fa-trash text-muted"></i>
                </a>
              </div>
            </div>
          </div>
        </div>
      }

      if (Config.features.projects !== true) {
        if (this.state.cart.vendors) {
          var add_rfp_btn = <a href="/rfps/create" className="btn btn-link">
            <span className="text-muted">or </span> create new
          </a>
        }
        if (this.state.cart.rfp && this.state.cart.rfp.is_template === true){
          var captionTxt = <p className="text-muted small">
            A new request will be created from this template
          </p>
        } else {
          var captionTxt = undefined;
        }
        var rfp = <div className="row">
          <div className="col-xs-12 list-header">
             Selected Request
          </div>
          <div className="col-sm-9 col-xs-12">
            <div className="rfp-select">
              <Select.Async ref="rfpSelect" onChange={this.onRFPSelect} name="rfp" loadOptions={this.searchRFP} placeholder="Search existing Request by name..." value={this.state.cart.rfp}/>
              {captionTxt}
            </div>
          </div>
          <div className="col-sm-3 col-xs-12 nopadding">
            {add_rfp_btn}
          </div>
        </div>
      }

      if (this.state.cart.vendors) {
        var add_vendors_btn = <span>(<a href="/vendors/">
          add suppliers
        </a>)</span>
      }

      return <Modal ref="modal" size="medium" show={this.state.isOpen} onModalClosed={Actions.hideCart}>
        <ModalBody>
          <div className="cart-body clearfix">
            <span className="cart-close-btn pull-right" data-dismiss="modal">
              <i className="fa fa-times"></i>
            </span>
            <h4>Shortlist</h4><hr/>
            <p className="text-muted meta-text">
              You can send a request to shortlisted suppliers here. You may choose to create a new request or send an existing request to suppliers
            </p>
            {loading}
            {request}
            {rfp}
            <br/><br/>
            <div className="row list-header">
              <div className="col-xs-12">
                Selected resources and suppliers {add_vendors_btn}
              </div>
            </div>
            <CartList {...this.state}/>
            {actions}
          </div>
        </ModalBody>
      </Modal>
    }
  }
});

document.addEventListener('DOMContentLoaded', function() {
var dropdown = document.getElementById('cart-dropdown');
if (dropdown !== null) {
  React.render(React.createFactory(Cart)(), dropdown);
}
}, false);

document.addEventListener('DOMContentLoaded', function() {
  var cartBody = document.getElementById('cart-body');
  if (cartBody !== null) {
    React.render(React.createFactory(CartBody)(), cartBody);
  }
}, false);

vetted.cartActions = Actions;
window.cartActions = Actions;

module.exports = {
  'Actions': Actions,
  'Cart': Cart
};
