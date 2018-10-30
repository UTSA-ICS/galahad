import {Component, OnInit} from '@angular/core';
import {MenuItem} from 'primeng/api';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  title = 'app';

  menuItems: MenuItem[];


  ngOnInit(): void {
    this.menuItems = [
      { label: 'Valors', routerLink: ['/views/valors-dashboard'] },
      { label: 'Virtues', routerLink: '/views/virtue-dashboard' },
      { label: 'Roles', routerLink: '/views/role-dashboard' },
      { label: 'Users', routerLink: '/views/user-dashboard' },
      { label: 'Transducers', routerLink: '/views/transducer-dashboard' },
      { label: 'Applications', routerLink: '/views/application-dashboard' },
      { label: 'Resources', routerLink: '/views/resource-dashboard' }
    ];
  }
}
