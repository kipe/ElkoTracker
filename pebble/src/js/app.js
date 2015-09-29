var UI = require('ui'),
    ajax = require('ajax');

var menu = new UI.Menu({
    sections: [{
        items: [{
            title: 'latitude',
            subtitle: '',
        },
        {
            title: 'longitude',
            subtitle: '',
        },
        {
            title: 'speed',
            subtitle: '',
        },
        {
            title: 'heading',
            subtitle: '',
        }]
    }]
});

function fetch_gps() {
    console.log('FETCHING GPS!')
    ajax({url: 'http://elko.hirvi.ovh/gps', type: 'json' }, function(data) {
        menu.item(0, 0, {title: 'latitude', subtitle: data.latitude.toFixed(5)});
        menu.item(0, 1, {title: 'longitude', subtitle: data.longitude.toFixed(5)});
        menu.item(0, 2, {title: 'speed', subtitle: data.speed.toFixed(1) + ' m/s'});
        menu.item(0, 3, {title: 'heading', subtitle: data.heading.toFixed(1)});
        setTimeout(fetch_gps, 10000);
    }, function(err) {
        console.log('ERRROR!!!!');
        setTimeout(fetch_gps, 10000);
    });
};

menu.show();
fetch_gps();
