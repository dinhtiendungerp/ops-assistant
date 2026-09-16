/// <summary>
/// Which location is a store and which is a warehouse. Read from LS Central master data, not from a filter typed on
/// NWV Agent Setup (Dung, 15/09/2026: "Central Warehouse Code" duplicated LSC Replen. Setup."Default Central Warehouse",
/// and "Store Location Filter" was never used by any calculation).
///
/// Store     = location listed in LSC Store."Location Code" (Store Type = Store), or in LSC Store Location (10001416),
///             the table LS uses when one store owns several locations.
/// Warehouse = LSC Replen. Setup."Default Central Warehouse" / "Default Warehouse 2" / "Default Warehouse 3", or a
///             Location with "LSC Location is a Warehouse" on. Demand at a warehouse is total outflow, not Sale lines.
/// Answers are cached per instance; calculations create one instance per run.
/// </summary>
codeunit 70112 "NWV Location Role"
{
    var
        StoreOf: Dictionary of [Code[10], Code[10]];
        WarehouseOf: Dictionary of [Code[10], Boolean];
        CentralWh: Code[10];
        Loaded: Boolean;

    procedure IsStore(LocationCode: Code[10]): Boolean
    begin
        Load();
        exit(StoreOf.ContainsKey(LocationCode));
    end;

    procedure StoreNo(LocationCode: Code[10]): Code[10]
    var
        No: Code[10];
    begin
        Load();
        if StoreOf.Get(LocationCode, No) then
            exit(No);
        exit('');
    end;

    procedure IsWarehouse(LocationCode: Code[10]): Boolean
    var
        Location: Record Location;
    begin
        Load();
        if WarehouseOf.ContainsKey(LocationCode) then
            exit(true);
        if Location.Get(LocationCode) and Location."LSC Location is a Warehouse" then begin
            WarehouseOf.Add(LocationCode, true);
            exit(true);
        end;
        exit(false);
    end;

    /// <summary>LSC Replen. Setup."Default Central Warehouse". Empty if LS Replenishment is not set up.</summary>
    procedure CentralWarehouse(): Code[10]
    begin
        Load();
        exit(CentralWh);
    end;

    procedure StoreCount(): Integer
    begin
        Load();
        exit(StoreOf.Count());
    end;

    local procedure Load()
    var
        Store: Record "LSC Store";
        StoreLocation: Record "LSC Store Location";
        ReplenSetup: Record "LSC Replen. Setup";
    begin
        if Loaded then
            exit;
        Loaded := true;
        Store.SetRange("Store Type", Store."Store Type"::Store);
        Store.SetFilter("Location Code", '<>%1', '');
        if Store.FindSet() then
            repeat
                if not StoreOf.ContainsKey(Store."Location Code") then
                    StoreOf.Add(Store."Location Code", Store."No.");
            until Store.Next() = 0;
        if StoreLocation.FindSet() then
            repeat
                if not StoreOf.ContainsKey(StoreLocation."Location Code") then
                    StoreOf.Add(StoreLocation."Location Code", StoreLocation."Store No.");
            until StoreLocation.Next() = 0;
        if ReplenSetup.Get() then begin
            CentralWh := ReplenSetup."Default Central Warehouse";
            AddWarehouse(ReplenSetup."Default Central Warehouse");
            AddWarehouse(ReplenSetup."Default Warehouse 2");
            AddWarehouse(ReplenSetup."Default Warehouse 3");
        end;
    end;

    local procedure AddWarehouse(LocationCode: Code[10])
    begin
        if (LocationCode <> '') and not WarehouseOf.ContainsKey(LocationCode) then
            WarehouseOf.Add(LocationCode, true);
    end;
}
