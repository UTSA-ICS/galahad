import { Injectable } from '@angular/core';
import {HttpClient, HttpHeaders} from '@angular/common/http';
import {Observable} from 'rxjs/index';
import {Virtue} from '../models/Virtue';
import {Role} from '../models/Role';
import {User} from '../models/User';
import {Resource} from '../models/Resource';
import {Application} from '../models/Application';
import {Transducer} from '../models/Transducer';

@Injectable({
  providedIn: 'root'
})
export class DataService {
  private baseUrl = 'http://localhost:3000'

  // API URL's
  private virtuesUrl = '/virtues';
  private rolesUrl = '/roles';
  private valorsUrl = '/valors';
  private usersUrl = '/users';
  private resourcesUrl = '/resources';
  private applicationsUrl = '/applications';
  private transducersUrl = '/transducers';
  private virtuesPerValor = '/virtues_per_valor';
  private migrationsPerVirtue = '/migrations_per_virtue';
  private virtuesPerRole = '/virtues_per_role';
  private messagesPerVirtue = '/messages_per_virtue';
  private messagesPerVirtuePerType = '/messages_per_virtue_per_type';
  private messagesPerType = '/messages_per_type';
  private transducerState = '/transducer_state';

  constructor(private http: HttpClient) { }

  // Get lists of objects

  getValors(): Observable<any> {
    return this.http.get(this.baseUrl + this.valorsUrl);
  }

  getVirtues(): Observable<Virtue[]> {
    return this.http.get<Virtue[]>(this.baseUrl + this.virtuesUrl);
  }

  getRoles(): Observable<Role[]> {
    return this.http.get<Role[]>(this.baseUrl + this.rolesUrl);
  }

  getUsers(): Observable<User[]> {
    return this.http.get<User[]>(this.baseUrl + this.usersUrl);
  }

  getResources(): Observable<Resource[]> {
    return this.http.get<Resource[]>(this.baseUrl + this.resourcesUrl);
  }

  getApplications(): Observable<Application[]> {
    return this.http.get<Application[]>(this.baseUrl + this.applicationsUrl);
  }

  getTransducers(): Observable<Transducer[]> {
    return this.http.get<Transducer[]>(this.baseUrl + this.transducersUrl);
  }

  // Specific value getters

  getVirtuesPerValor(): any {
    return this.http.get(this.baseUrl + this.virtuesPerValor);
  }

  getMigrationsPerVirtue(): any {
    return this.http.get(this.baseUrl + this.migrationsPerVirtue);
  }

  getVirtuesPerRole(): any {
    return this.http.get(this.baseUrl + this.virtuesPerRole);
  }

  getMessagesPerVirtue(timeperiod: string): any {
    return this.http.get(this.baseUrl + this.messagesPerVirtue + '/' + timeperiod);
  }

  getMessagesPerVirtuePerType(timeperiod: string): any {
    return this.http.get(this.baseUrl + this.messagesPerVirtuePerType + '/' + timeperiod);
  }

  getMessagesPerType(virtueId: string, timeperiod: string): any {
    return this.http.get(this.baseUrl + this.messagesPerType + '/' + virtueId + '/' + timeperiod);
  }

  getTransducerState(): any {
    return this.http.get(this.baseUrl + this.transducerState);
  }
}
