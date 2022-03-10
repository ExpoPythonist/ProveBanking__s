_inExec.register({
  name: 'vendor_profile',
  routes: ['/vendors/[\\w.-]+/$'],
  initialize: function($container){
    this.update();
  },
  update: function(){
    //alert('fuck balls');
    var that = this;


    $(".show-more span").on("click", function() {
      var $content = $(this).parent().prev("div.content");
      var linkText = $(this).text().toUpperCase();

      if(linkText === "SHOW MORE..."){
          linkText = "Show less";
          $content.removeClass("hideContent").addClass("showContent");
      } else {
          linkText = "Show more...";
          $content.removeClass("showContent").addClass("hideContent");
      };

      $(this).text(linkText);
    });
  },
  destroy: function(){
  }
});
