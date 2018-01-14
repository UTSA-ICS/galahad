// initialize app
// and ...
nw.Window.open('index.html', {}, function(win) {
  
});

// Create a tray icon
var tray = new nw.Tray({ title: 'Tray', icon: './assets/img/virtue.png' });

// Give it a menu
var menu = new nw.Menu();
menu.append(new nw.MenuItem({ type: 'checkbox', label: 'box1' }));
tray.menu = menu;
