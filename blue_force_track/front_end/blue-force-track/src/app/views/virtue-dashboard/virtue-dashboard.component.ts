import { Component, OnInit } from '@angular/core';

@Component({
  selector: 'app-virtue-dashboard',
  templateUrl: './virtue-dashboard.component.html',
  styleUrls: ['./virtue-dashboard.component.css']
})
export class VirtueDashboardComponent implements OnInit {

  // Bar chat config
  barData: any[];
  barView: any[] = [700, 400];

  // options
  barShowXAxis = true;
  barShowYAxis = true;
  barGradient = false;
  barShowLegend = true;
  barShowXAxisLabel = true;
  barXAxisLabel = 'Virtue';
  barShowYAxisLabel = true;
  barYAxisLabel = 'Migrations Today';

  barColorScheme = {
    domain: ['#5AA454', '#A10A28', '#C7B42C', '#AAAAAA']
  };

  // Table Config
  cols = [
    { field: 'dn', header: 'Domain Name' },
    { field: 'cusername', header: 'Username' },
    { field: 'ou', header: 'Organizational Unit' },
    { field: 'cipAddress', header: 'IP Address' },
    { field: 'cstate', header: 'State' },
    { field: 'croleId', header: 'Role ID' },
    { field: 'cid', header: 'Id'}
  ];

  tableData: any[];

  constructor() { }

  ngOnInit() {
    this.barData = [
      {
        name: 'Virtue_1',
        value: '4'
      },
      {
        name: 'Virtue_2',
        value: '6'
      },
      {
        name: 'Virtue_3',
        value: 0
      },
      {
        name: 'Virtue_4',
        value: 3
      }
    ]

    this.tableData = [
      {
        dn: 'cusername=fpatwa,cn=users,ou=virtue,dc=canvas,dc=virtue,dc=com',
        ou: 'virtue',
        cusername: 'fpatwa',
        cid: 'Virtue_SecurityTestRole_1539878119',
        cipAddress: '10.91.0.1',
        cstate: 'RUNNING',
        croleId: 'SecurityTestRole1539876260',
        cappIds: [],
        cresIds: [],
        ctransIds: [],
        cauthRoleIds: ['SecurityTestRole1539876260', 'Role_2', 'Role_3', 'Role_4']
      }
    ];
  }

}
