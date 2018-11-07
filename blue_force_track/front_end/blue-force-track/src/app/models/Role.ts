export class Role {
  private _dn: string;
  private _name: string;
  private _objectClass: string;
  private _cstate: string;
  private _cid: string;
  private _cversion: string;
  private _ou: string;
  private _cappIds: string[];
  private _cstartResIds: string[];
  private _cstartTransIds: string[];


  constructor() {
  }


  get dn(): string {
    return this._dn;
  }

  set dn(value: string) {
    this._dn = value;
  }

  get name(): string {
    return this._name;
  }

  set name(value: string) {
    this._name = value;
  }

  get objectClass(): string {
    return this._objectClass;
  }

  set objectClass(value: string) {
    this._objectClass = value;
  }

  get cstate(): string {
    return this._cstate;
  }

  set cstate(value: string) {
    this._cstate = value;
  }

  get cid(): string {
    return this._cid;
  }

  set cid(value: string) {
    this._cid = value;
  }

  get cversion(): string {
    return this._cversion;
  }

  set cversion(value: string) {
    this._cversion = value;
  }

  get ou(): string {
    return this._ou;
  }

  set ou(value: string) {
    this._ou = value;
  }

  get cappIds(): string[] {
    return this._cappIds;
  }

  set cappIds(value: string[]) {
    this._cappIds = value;
  }

  get cstartResIds(): string[] {
    return this._cstartResIds;
  }

  set cstartResIds(value: string[]) {
    this._cstartResIds = value;
  }

  get cstartTransIds(): string[] {
    return this._cstartTransIds;
  }

  set cstartTransIds(value: string[]) {
    this._cstartTransIds = value;
  }
}
