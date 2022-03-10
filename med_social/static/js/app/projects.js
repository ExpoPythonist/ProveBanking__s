Messenger.options = {
    extraClasses: 'messenger-fixed messenger-on-bottom messenger-on-right',
    theme: 'flat',
};

_inExec.register({
  name: 'projects',
  routes: ['^/projects/$','^/projects/\\d+/$', '^/staffing/r/\\d+/$'],
  initialize: function($container){
    var that = this;
    this.$document = $(document);
    this.$container = $container;

    this.client = new $.RestClient('/api/');
    this.client.add('projects');
    this.client.projects.addVerb('archive', 'POST', {url: 'archive/'});
    this.client.projects.addVerb('unarchive', 'POST', {url: 'unarchive/'});

    this.onStaffAdded = function(ev, data){
      data.$result.parents('.field-nested').find('.btn-staff-status').removeClass('hide');
      data.$result.parents('.field-nested').find('.fa-level-up').addClass('hide');
      that.updateProjectCost();
    };

    this.onStaffRemoved = function(ev, data){
      data.$result.parents('.field-nested').find('.fa-level-up').removeClass('hide');
      data.$result.parents('.field-nested').find('.btn-staff-status').addClass('hide');
      that.updateProjectCost();
    };

    this.projectStaffAdd = function(ev, data){
      var $form = $('#project-staff-user-form');
      var $project = $form.find('#project-object .project-card');
      $project_id = $project.data("project-id");
      $($project_id).replaceWith($project);
      $form.parents('.modal').modal('hide');
      that.update();
    }

    this.update();
  },
  update: function(){
    this.$totalCost = $('.project-cost');
    this.destroy();
    this.setup();

  },
  destroy: function(){
    _inExec.modules.events.off('staffing:add', this.onStaffAdded);
    _inExec.modules.events.off('staffing:remove', this.onStaffRemoved);
    _inExec.modules.events.off('form:success#project-staff-user-form', this.projectStaffAdd);
    $('.btn-archive-project').off('click', $.proxy(this.archiveProject, this));
    $('.btn-unarchive-project').off('click', $.proxy(this.unarchiveProject, this));
    $('.propose-delete-btn').off('click');
    $('#archive-show-btn').off('click');

  },
  setup: function(){

    $('.btn-archive-project').on('click', $.proxy(this.archiveProject, this));
    $('.btn-unarchive-project').on('click', $.proxy(this.unarchiveProject, this));

    $('.propose-delete-btn').on('click', function(ev){
      $.post($(ev.target).attr('data-url'), { pk : $(ev.target).attr('data-pk')});
      $(ev.target).closest('.staffed-user-wrapper-card').remove();
      var notif = window.Messenger().post({
        'showCloseButton': true,
        'type': 'success',
        'message': 'Candidate unstaffed successfully'
      });
    });

    $('#archive-show-btn').on('click', function(ev){
        if($(ev.target).text() == 'Show archived projects') {
          $(ev.target).text('Hide archived projects');
        } else {
          $(ev.target).text('Show archived projects');
        }
    });

    var that = this;
    _inExec.modules.events.on('staffing:add', this.onStaffAdded);
    _inExec.modules.events.on('staffing:remove', this.onStaffRemoved);
    _inExec.modules.events.on('form:success#project-staff-user-form', this.projectStaffAdd);
  },

  updateProjectCost: function(){
    var projectId = this.$totalCost.attr('data-project-id');
    this.$totalCost.load('/projects/' + projectId + '/budget/');
  },

  unarchiveProject: function(ev){
      ev.preventDefault();
      var that = this;
      var $target = $(ev.target);
      var $project = $target.parents('.project-item');
      var $footer = $project.next('.project-footer');
      var pk = $project.attr('data-pk');
      this.client.projects.unarchive(pk, {}).done(function(){
        $project.removeClass('hide');
        $footer.removeClass('hide');
        $target.removeClass('btn-unarchive-project').addClass('btn-archive-project');
      });
    },

  archiveProject: function(ev){
    ev.preventDefault();
    var that = this;
    var $target = $(ev.target);
    var $project = $target.parents('.project-item');
    var $footer = $project.next('.project-footer');
    var pk = $project.attr('data-pk');
    var title = $project.attr('data-title');

    var notif = window.Messenger().post({
      'showCloseButton': true,
      'type': 'info',
      'message': 'Archiving "' + title + '"'
    });

    this.client.projects.archive(pk, {}).done(function(){
      $project.addClass('hide');
      $target.removeClass('btn-archive-project').addClass('btn-unarchive-project');
      $footer.addClass('hide');
      notif.update({type: "success",
        message: 'Archived "' + title  + '"',
        actions: {
          undo: {
            label: "Undo",
            action: function(){
              that.unarchiveProject(ev);
              notif.hide();
            }
          }
        }
      });
    });

  },
});




_inExec.register({
  name: 'createProject',
  routes: ['^/projects/\\d+/edit/$', '^/projects/create/$'],
  initialize: function($container){
    this.setUp();
  },
  update: function(){
    this.setUp();
  },
  destroy: function(){
  },
  toggleStatusDescription: function() {
    var selected = this.$statusField.val();
    var selector = '#status-' + selected;
    this.$statusDescriptions.find('.status').addClass('hide');
    this.$statusDescriptions.find(selector).removeClass('hide');
  },
  setUp: function(){
    var that = this;
    this.$projectForm = $('#project-form');
    this.$statusDescriptions = $('#status-descriptions');
    this.$statusField = $('#id_status');
    var instanceName = this.$projectForm.attr('id') + '_' + 'id_allowed_vendors';
    this.$visibility = $('#id_visibility');
    this.$visibility.show();
    this.toggleStatusDescription();
    this.$statusField.on('change', function(e){
      that.toggleStatusDescription();
    });
    this.$projectForm.on('submit', function(e) {
      if (that.$visibility.is(':checked') == false) {
        if (that.$vendors.getValue().length == 0) {
          e.preventDefault();
          e.stopPropagation();
          bootbox.dialog({
            title: "Missing Vendors",
            message: "You must make the project visible to all or invite some vendors to the project",
            buttons: {
              no: {
                label: 'Back',
                className: ' ',
                iconClass: 'fa-chevron-left',
              }
            }
          })
        }
      }
    });
  }
});


_inExec.register({
  name: 'projects-staffing-crud',
  routes: ['^/projects/\\d+/$', '^/staffing/r/\\d+/$'],
  initialize: function($container){
    this.update();
  },

  update: function(){
    this.destroy();
    this.setup();
  },

  destroy: function(){
    $('.new-request-btn').off();
    $('.new-request').find('form').off();
    _inExec.modules.events.off('newItem:' + 'staffing-request', $.proxy(this.onRequestCreated, this));
  },

  setup: function(){
    this.$requestList = $('#request-list');
    this.$createForm = $('.new-request');
    this.$createRequestBtn = $('.new-request-btn');
    this.$createRequestBtn.on('click', $.proxy(this.showRequestForm, this));
    this.$createForm.find('form').on('reset', $.proxy(this.hideRequestForm, this));
    _inExec.modules.events.on('newItem:' + 'staffing-request', $.proxy(this.onRequestCreated, this));
  },

  onRequestCreated: function(ev){
    $result = ev.$result;
    this.$requestList.prepend($result);
    this.hideRequestForm();
    _inExec.modules.utils.animate($result, 'fadeInDown');
    this.$createRequestBtn.addClass('btn-o btn-dash');

    var $placeholder = this.$requestList.find('.request-placeholder');
    if ($placeholder.length  !== 0) {
      $placeholder.animate('fadeOutDown', function(){
        $placeholder.remove();
      });
    }
    _inExec.modules.autocomplete.$instances['inline-request-form_id_role'].$selectize.setValue();
    _inExec.modules.autocomplete.$instances['inline-request-form_id_categories'].$selectize.setValue();
    this.update();
  },

  showRequestForm: function(){
    var that = this;
    that.$createRequestBtn.addClass('hide');
    that.$createForm.removeClass('hide');
  },

  hideRequestForm: function(){
    this.$createForm.addClass('hide');
    this.$createRequestBtn.removeClass('hide');
  }
});
