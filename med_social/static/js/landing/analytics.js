$(document).ready(function(){
  if(mixpanel !== undefined && mixpanel !== null){
    mixpanel.track_links("#linkedinSignupButton", "Signup", {'medium': 'linkedin'});
    mixpanel.track_links("#linkedinLoginButton", "Login", {'medium': 'linkedin'});
    mixpanel.track_links("#aboutLink", "About Us", {'source': 'landing'});
    mixpanel.track_links("#contactLink", "Contact Us", {'source': 'landing'});
    mixpanel.track_links(".btn-landing-cta", "Request Demo", {'source': 'landing'});
  }
});
