$.ajaxSettings.traditional = true;
var Client = new $.RestClient('/api/', {stringifyData: true});

// vendors
Client.add('vendors');
Client.vendors.addVerb('add_keyword', 'POST', {url: 'add_keyword/'});
Client.vendors.addVerb('remove_keyword', 'POST', {url: 'remove_keyword/'});
Client.vendors.add('news');

// vendors
Client.add('users');

// Aggregator
Client.add('aggregator');

//Channels
Client.add('channels');
Client.channels.addVerb('add_message', 'POST', {url: 'add_message/'});

// projects
Client.add('projects');
Client.projects.addVerb('archive', 'POST', {url: 'archive/'});
Client.projects.addVerb('unarchive', 'POST', {url: 'unarchive/'});


// shortlist cart
Client.add('cart');
Client.cart.addVerb('checkout', 'POST', {url: 'checkout/'});
Client.cart.addVerb('add_person', 'POST', {url: 'add_person/'});
Client.cart.addVerb('add_vendor', 'POST', {url: 'add_vendor/'});
Client.cart.addVerb('add_request', 'POST', {url: 'add_request/'});
Client.cart.addVerb('add_rfp', 'POST', {url: 'add_rfp/'});
Client.cart.addVerb('remove_person', 'POST', {url: 'remove_person/'});
Client.cart.addVerb('remove_vendor', 'POST', {url: 'remove_vendor/'});
Client.cart.addVerb('remove_request', 'POST', {url: 'remove_request/'});
Client.cart.addVerb('remove_rfp', 'POST', {url: 'remove_rfp/'});
Client.cart.addVerb('set_person_status', 'POST', {url: 'set_person_status/'});


// locations
Client.add('locations');


// categories
Client.add('categories');

module.exports.Client = Client;
window.RestClient = Client;
