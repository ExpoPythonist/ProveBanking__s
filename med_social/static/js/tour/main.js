(function(){
  _inExec.register({
    name: 'tour',
    initialize: function(){
      this.trip = new Trip([
        {
          sel : $(".panel-consultant"),
          content : "",
          expose : true,
          delay: 2000,
          showNavigation: true,
        },
        {
          sel : $("#editProfileBtn"),
          content : "Click to edit your basic information",
          expose : true,
          delay: -1,
          showNavigation: true,
        },
        {
          sel : $("#profileFormContainer"),
          content : "Click to edit your basic information",
          expose : true,
          delay: -1,
          showNavigation: true,
        },
      ]);
//      this.trip.start();
    }
  });
})();
