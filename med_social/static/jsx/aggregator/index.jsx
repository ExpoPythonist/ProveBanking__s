var React = require('react'),
    Reflux = require('reflux'),
    classNames = require('classnames'),
    moment = require('moment'),

    LoadingDots = require('../common/loading-dots.jsx').LoadingDots,
    RestClient = require('../common/rest-clients.jsx').Client,
    utils = require('../libs/utils.jsx'),
    Modal = require('../common/modals.jsx').Modal,
    ModalBody = require('../common/modals.jsx').Body,
    ModalFooter = require('../common/modals.jsx').Footer,
    ModalHeader = require('../common/modals.jsx').Header;


var Actions = Reflux.createActions({
  "fetchForVendor": {children: ['completed', 'failed']},
  "addNewKeyword": {children: ['completed', 'failed']},
  "removeKeyword": {children: ['completed', 'failed']},
});


Actions.fetchForVendor.listen(function(vendor_id){
  var that = this;
  RestClient.vendors.news.read(vendor_id)
    .done(function(response){that.completed(vendor_id, response)})
    .fail(function(xhr, text, error){that.failed(vendor_id, text, error)});
});


Actions.addNewKeyword.listen(function(vendor_id, keyword){
  var that = this;
  RestClient.vendors.add_keyword(vendor_id, {keyword: keyword})
    .done(function(response){that.completed(vendor_id, keyword, response)})
    .fail(function(xhr, text, error){that.failed(vendor_id, keyword, text, error)});
});


Actions.removeKeyword.listen(function(vendor_id, keyword){
  var that = this;
  RestClient.vendors.remove_keyword(vendor_id, {keyword: keyword})
    .done(function(response){that.completed(vendor_id, keyword, response)})
    .fail(function(xhr, text, error){that.failed(vendor_id, keyword, text, error)});
});


var Store = Reflux.createStore({
  listenables: Actions,

  init: function(){
    this.data = {};
  },

  onFetchForVendorCompleted: function(vendor_id, response){
    this.data[vendor_id] = response;
    this.trigger(this.data);
  },

  onAddNewKeywordCompleted: function(vendor_id, keyword, response){
    this.data[vendor_id] = response;
    this.trigger(this.data);
  },

  onRemoveKeywordCompleted: function(vendor_id, keyword, response){
    this.data[vendor_id] = response;
    this.trigger(this.data);
  },
});


var SourceDetails = React.createClass({
  mixins: [
    Reflux.listenTo(Actions.addNewKeyword.completed, "onNewKeywordDone"),
    Reflux.listenTo(Actions.addNewKeyword.failed, "onNewKeywordDone"),
    Reflux.listenTo(Actions.removeKeyword.completed, "onRemoveKeywordDone"),
    Reflux.listenTo(Actions.removeKeyword.failed, "onRemoveKeywordDone")
  ],

  onNewKeywordDone: function(vendor_id, keyword){
    if ((vendor_id === this.props.vendor_id) && (keyword === this.state.addingKeyword)) {
      this.setState({addingKeyword: null});
    }
  },

  onRemoveKeywordDone: function(vendor_id, keyword){
    if ((vendor_id === this.props.vendor_id)) {
      this.setState({removingKeywords: _.without(this.state.removingKeywords, keyword)})
    }
  },

  getInitialState: function(){
    return {isOpen: true, addingKeyword: null, removingKeywords: []};
  },

  removeKeyword: function(keyword){
    var removing = this.state.removingKeywords;
    removing.push(keyword);
    this.setState({removingKeywords: removing});
    Actions.removeKeyword(this.props.vendor_id, keyword);
  },

  addNewKeyword: function(e){
    e.preventDefault();
    e.stopPropagation();
    var keyword = this.refs.keywordInput.getDOMNode().value.trim();
    if (keyword.length > 0) {
      this.setState({addingKeyword: keyword});
      Actions.addNewKeyword(this.props.vendor_id, keyword);
    }
  },

  render: function(){
    var that = this;
    if (this.state.addingKeyword != null) {
      var newKeyword = <div>
        <small>Adding new keyword <b>{this.state.addingKeyword}</b> ...</small>
      </div>
    } else {
      var newKeyword = <form className="form-mobile form-horizontal" onSubmit={this.addNewKeyword}>
        <div className="form-group row">
          <div className="controls">
            <div className="col-xs-6 nopadding">
              <input className="form-control" type="text" placeholder="new search keyword" ref="keywordInput"/>
            </div>
            <div className="col-xs-6">
              <button className="btn btn-sm btn-primary" type="submit">add keyword</button>
            </div>
          </div>
        </div>
      </form>
    }
    return <Modal ref="modal" size="medium" show={this.state.isOpen} onModalClosed={this.props.onHide}>
      <ModalBody>
        <div className="cart-body clearfix">
          <span className="cart-close-btn pull-right" data-dismiss="modal">
            <i className="fa fa-times"></i>
          </span>
          <h4>Sources and Search Terms</h4><hr/>
          <p className="text-muted meta-text">
            You can add or remove search keywords to help us aggregate news for the supplier.
          </p>
          <h5><b>Google News</b></h5>
          <div className="panel panel-default">
            <div className="panel-body">
              <br/>
              {this.props.keywords.map(function(K){
                return <div className="btn-group" role="group" aria-label="...">
                  <button type="button" className="btn btn-default btn-xs">{K}</button>
                  <button type="button" className="btn btn-default btn-xs" onClick={function(){that.removeKeyword(K)}}><i className="fa fa-remove"></i></button>&nbsp;&nbsp;
                </div>
              })}
              {newKeyword}
            </div>
          </div>
        </div>
      </ModalBody>
    </Modal>
  }
});


var List = React.createClass({
  mixins: [Reflux.listenTo(Store, "onStoreChanged")],

  onStoreChanged: function(data){
    this.setState({news: data[this.props.vendor_id] || null});
    if (this.state.news && this.state.news.is_updating === true) {
      setTimeout(this.refresh, 4000);
    }
  },

  refresh: function(){
    Actions.fetchForVendor(this.props.vendor_id);
  },

  getInitialState: function(){
    return {
      news: Store.data[this.props.vendor_id] || null,
      sourceDetails: null,
      listLimit: 3
    };
  },

  componentDidMount: function() {
    window.News = this;
    Actions.fetchForVendor(this.props.vendor_id);
    this.refresh();
  },

  showSourceDetails: function(e){
    e.preventDefault();
    e.stopPropagation();
    this.setState({showSourceDetails: true});
  },

  hideSourceDetails: function(){
    this.setState({showSourceDetails: false});
  },

  getSourceName: function(source){
    return {
      google: 'Google News',
      yahoo: 'Yahoo News',
      faroo: 'Faroo News'
    }[source];
  },

  getSourceURL: function(source, keyword){
    return {
      google: 'https://news.google.com/?q=' + keyword,
      yahoo: 'https://news.search.yahoo.com/search?p=' + keyword,
      faroo: 'https://www.faroo.com/#q=' + keyword + '&src=news'
    }[source]
  },

  toggleLimit: function(){
    if (this.state.listLimit === null) {
      this.setState({listLimit: 3});
    } else {
      this.setState({listLimit: null});
    }
  },

  render: function(){
    var that = this;
    if (this.state.news === null) {
      var newsFeed = <span><LoadingDots/></span>;
    } else if (this.state.news.results.length === 0) {
      if (this.state.news.is_updating === true) {
        var tagLine = <h6>Our army of robots are working to get you the latest news<LoadingDots/></h6>
      } else {
        var tagLine = <h6>If no news appears, try <a href="#" onClick={that.showSourceDetails}>changing the search keywords</a> to refine the results.</h6>
      }
      var newsFeed = <div className="blank-slate">
          <div className="repr">
            <i className='fa fa-2x fa-newspaper-o fa-2x'>&nbsp;</i>
          </div>
          <h5 className="slate-title">News will appear here</h5>
          {tagLine}
        </div>
    } else {
      var smallKeywords = this.state.news.keywords.map(function(key){
        return key.toLowerCase();
      });
      if (this.state.listLimit) {
        var moreBtnLabel = 'show more';
        var results = this.state.news.results.slice(0, 3);
      } else {
        var moreBtnLabel = 'show less';
        var results = this.state.news.results;
      }
      var newsFeed = <div className="news-feed row">
        {results.map(function(result){
          var summary = result.meta.summary;
          _.each(that.state.news.keywords, function(K){
            summary = summary.replace(new RegExp('(' + K + ')', 'gi'), '<b>$1</b>');
          });
          if (result.meta.date) {
            var date = moment(new Date(result.meta.date)).calendar();
          } else {
            var date = null;
          }
          return <div className="news-item col-xs-12" key={result.id}>
            <h4><a href={result.meta.url} target="_blank">{result.meta.title}</a></h4>
            <div className="row meta">
              <div className="col-xs-6">
                {result.meta.site} - {date}
              </div>
            </div>
            <p className="summary" dangerouslySetInnerHTML={{__html: summary}} />
          <div className="row meta">
              <div className="col-xs-12">
                {result.meta.sources.map(function(source){
                  return <div>
                    {that.getSourceName(source)} for&nbsp;
                    {result.keywords.map(function(keyword){
                      return <a className="no-link-style" href={that.getSourceURL(source, keyword)} target="_blank">{keyword}</a>
                    })}
                  </div>
                })}
              </div>
            </div>
          </div>
        })}
        <div className="col-xs-12 text-center">
          <button className="btn btn-primary btn-o btn-sm" onClick={this.toggleLimit}>{moreBtnLabel}</button>
        </div>
      </div>
    }

    if (this.state.showSourceDetails === true) {
      var sourceModal = <SourceDetails vendor_id={this.props.vendor_id} keywords={this.state.news.keywords} onHide={this.hideSourceDetails}/>
    }

    if (this.state.news && this.state.news.is_updating === true) {
      var isUpdating = <span>(updating <LoadingDots/>)</span>;
    }

    if (vetted.config.user.is_client) {
      var changeTerms = <a href="#" onClick={this.showSourceDetails}>edit search terms</a>
    }

    if (this.state.news && this.state.news.keywords) {
      var title = <span>News search results for: <span className="emphasize">{this.state.news.keywords.join(', ')}</span></span>
    }

    return <div>
      {sourceModal}
      <div className="row">
        <div className="col-xs-6 ">
          <h6 className="section-title text-uppercase">News & articles</h6>
        </div>
        <div className="col-xs-6 text-right">
        </div>
      </div>
      <div className="panel panel-default panel-card">
        <div className="panel-body">
          <div className="row">
            <div className="col-xs-6 block-meta">
              {title} {isUpdating}
            </div>
            <div className="col-xs-6 text-right block-meta">
              <span className="text-lowercase lighter">{changeTerms}</span>
            </div>
            <div className="col-xs-12">
              <hr className="thin"/>
              {newsFeed}
            </div>
          </div>
        </div>
      </div>
    </div>
  }
});

document.addEventListener('DOMContentLoaded', function() {
  var root = document.getElementById('aggregator-list');
  if (root !== null) {
    var vendor_id = root.getAttribute('data-vendor-id');
    var list = React.createFactory(List)({vendor_id: vendor_id});
    React.render(list, root);
  };
}, false);

module.exports = {'List': List};
