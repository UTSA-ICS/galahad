import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-user-dashboard',
  templateUrl: './user-dashboard.component.html',
  styleUrls: ['./user-dashboard.component.css']
})
export class UserDashboardComponent implements OnInit {

  // Bar chat config
  barData: any[];
  barView: any[] = [700, 400];

  // options
  barShowXAxis = true;
  barShowYAxis = true;
  barGradient = false;
  barShowLegend = true;
  barShowXAxisLabel = true;
  barXAxisLabel = 'Valor';
  barShowYAxisLabel = true;
  barYAxisLabel = 'Virtues';

  barColorScheme = {
    domain: ['#5AA454', '#A10A28', '#C7B42C', '#AAAAAA']
  };

  // Table Config
  cols = [
    { field: 'dn', header: 'Domain Name' },
    { field: 'cusername', header: 'Username' },
    { field: 'ou', header: 'Organizational Unit' }
  ];

  tableData: any[];

  constructor() { }

  ngOnInit() {
    this.tableData = [
      {
        dn: 'cusername=fpatwa,cn=users,ou=virtue,dc=canvas,dc=virtue,dc=com',
        ou: 'virtue',
        cauthRoleIds: ['SecurityTestRole1539876260', 'Role_2', 'Role_3', 'Role_4'],
        cusername: 'fpatwa'
      }
    ];

    this.barData = [
      {
        name: 'Admin',
        value: 4
      }
    ];
  }

}
