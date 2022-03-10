import initClients from './vendors/clients';

// now we use JQuery globally (via RequireJS)
import 'script!jquery-validation/dist/jquery.validate.js';




function init() {
    initClients();
}


init();