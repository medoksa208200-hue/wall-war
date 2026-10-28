package com.mohamed.wallwar;

import android.Manifest;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.LocationManager;
import android.net.Uri;
import android.provider.Settings;
import androidx.core.content.ContextCompat;
import androidx.core.location.LocationManagerCompat;
import com.getcapacitor.JSArray;
import android.os.Build;
import androidx.annotation.NonNull;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;
import com.google.android.gms.nearby.Nearby;
import com.google.android.gms.nearby.connection.AdvertisingOptions;
import com.google.android.gms.nearby.connection.ConnectionInfo;
import com.google.android.gms.nearby.connection.ConnectionLifecycleCallback;
import com.google.android.gms.nearby.connection.ConnectionResolution;
import com.google.android.gms.nearby.connection.ConnectionsClient;
import com.google.android.gms.nearby.connection.DiscoveredEndpointInfo;
import com.google.android.gms.nearby.connection.DiscoveryOptions;
import com.google.android.gms.nearby.connection.EndpointDiscoveryCallback;
import com.google.android.gms.nearby.connection.Payload;
import com.google.android.gms.nearby.connection.PayloadCallback;
import com.google.android.gms.nearby.connection.PayloadTransferUpdate;
import com.google.android.gms.nearby.connection.Strategy;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Two-phone play over Bluetooth / Wi-Fi Direct with Google Nearby Connections — no internet needed.
 * JS: ensure() → advertise({name}) on the host, discover() + connect({id,name}) on the guest,
 * then send({data}) and listen for found / lost / connected / failed / disconnected / message.
 */
@CapacitorPlugin(
    name = "WallNearby",
    permissions = {
        @Permission(alias = "coarse", strings = { Manifest.permission.ACCESS_COARSE_LOCATION }),
        @Permission(alias = "fine", strings = { Manifest.permission.ACCESS_FINE_LOCATION }),
        @Permission(alias = "scan", strings = { Manifest.permission.BLUETOOTH_SCAN }),
        @Permission(alias = "adv", strings = { Manifest.permission.BLUETOOTH_ADVERTISE }),
        @Permission(alias = "conn", strings = { Manifest.permission.BLUETOOTH_CONNECT }),
        @Permission(alias = "wifi", strings = { Manifest.permission.NEARBY_WIFI_DEVICES })
    }
)
public class WallNearbyPlugin extends Plugin {
    private static final String SERVICE_ID = "com.mohamed.wallwar.game";
    private static final Strategy STRATEGY = Strategy.P2P_POINT_TO_POINT;
    private ConnectionsClient client;
    private String peer;

    @Override
    public void load() {
        client = Nearby.getConnectionsClient(getContext());
    }

    /** permission (by alias) this Android version needs for Nearby Connections, checked against the OS itself */
    private Map<String, String> needed() {
        Map<String, String> m = new LinkedHashMap<>();
        m.put("coarse", Manifest.permission.ACCESS_COARSE_LOCATION);
        m.put("fine", Manifest.permission.ACCESS_FINE_LOCATION);
        if (Build.VERSION.SDK_INT >= 31) {
            m.put("scan", Manifest.permission.BLUETOOTH_SCAN);
            m.put("adv", Manifest.permission.BLUETOOTH_ADVERTISE);
            m.put("conn", Manifest.permission.BLUETOOTH_CONNECT);
        }
        if (Build.VERSION.SDK_INT >= 33) m.put("wifi", Manifest.permission.NEARBY_WIFI_DEVICES);
        return m;
    }

    private List<String> missingAliases() {
        List<String> out = new ArrayList<>();
        for (Map.Entry<String, String> e : needed().entrySet()) {
            if (ContextCompat.checkSelfPermission(getContext(), e.getValue()) != PackageManager.PERMISSION_GRANTED) out.add(e.getKey());
        }
        return out;
    }

    private JSObject status() {
        JSObject r = new JSObject();
        List<String> miss = missingAliases();
        r.put("granted", miss.isEmpty());
        r.put("missing", new JSArray(miss));
        LocationManager lm = (LocationManager) getContext().getSystemService(Context.LOCATION_SERVICE);
        r.put("locationOn", lm == null || LocationManagerCompat.isLocationEnabled(lm));
        BluetoothManager bm = (BluetoothManager) getContext().getSystemService(Context.BLUETOOTH_SERVICE);
        BluetoothAdapter ad = bm == null ? null : bm.getAdapter();
        r.put("bluetoothOn", ad != null && ad.isEnabled());
        return r;
    }

    @PluginMethod
    public void ensure(PluginCall call) {
        List<String> miss = missingAliases();
        if (miss.isEmpty()) {
            call.resolve(status());
            return;
        }
        requestPermissionForAliases(miss.toArray(new String[0]), call, "permsDone");
    }

    @PermissionCallback
    private void permsDone(PluginCall call) {
        call.resolve(status());
    }

    @PluginMethod
    public void openSettings(PluginCall call) {
        try {
            String what = call.getString("what", "app");
            Intent i;
            if ("location".equals(what)) i = new Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS);
            else if ("bluetooth".equals(what)) i = new Intent(Settings.ACTION_BLUETOOTH_SETTINGS);
            else {
                i = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
                i.setData(Uri.fromParts("package", getContext().getPackageName(), null));
            }
            i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(i);
            call.resolve();
        } catch (Exception e) {
            call.reject(String.valueOf(e.getMessage()));
        }
    }

    @PluginMethod
    public void advertise(PluginCall call) {
        String name = call.getString("name", "Player");
        AdvertisingOptions opts = new AdvertisingOptions.Builder().setStrategy(STRATEGY).build();
        client.startAdvertising(name, SERVICE_ID, lifecycle, opts)
            .addOnSuccessListener(v -> call.resolve())
            .addOnFailureListener(e -> call.reject(String.valueOf(e.getMessage())));
    }

    @PluginMethod
    public void discover(PluginCall call) {
        DiscoveryOptions opts = new DiscoveryOptions.Builder().setStrategy(STRATEGY).build();
        client.startDiscovery(SERVICE_ID, discovery, opts)
            .addOnSuccessListener(v -> call.resolve())
            .addOnFailureListener(e -> call.reject(String.valueOf(e.getMessage())));
    }

    @PluginMethod
    public void connect(PluginCall call) {
        String id = call.getString("id");
        if (id == null) {
            call.reject("missing id");
            return;
        }
        String name = call.getString("name", "Player");
        client.requestConnection(name, id, lifecycle)
            .addOnSuccessListener(v -> call.resolve())
            .addOnFailureListener(e -> {
                JSObject d = new JSObject();
                d.put("reason", String.valueOf(e.getMessage()));
                notifyListeners("failed", d);
                call.reject(String.valueOf(e.getMessage()));
            });
    }

    @PluginMethod
    public void send(PluginCall call) {
        String data = call.getString("data", "");
        if (peer == null) {
            call.reject("not connected");
            return;
        }
        client.sendPayload(peer, Payload.fromBytes(data.getBytes(StandardCharsets.UTF_8)));
        call.resolve();
    }

    @PluginMethod
    public void stop(PluginCall call) {
        stopAll();
        call.resolve();
    }

    private void stopAll() {
        if (client == null) return;
        client.stopAdvertising();
        client.stopDiscovery();
        client.stopAllEndpoints();
        peer = null;
    }

    @Override
    protected void handleOnDestroy() {
        stopAll();
    }

    private final EndpointDiscoveryCallback discovery = new EndpointDiscoveryCallback() {
        @Override
        public void onEndpointFound(@NonNull String id, @NonNull DiscoveredEndpointInfo info) {
            JSObject d = new JSObject();
            d.put("id", id);
            d.put("name", info.getEndpointName());
            notifyListeners("found", d);
        }

        @Override
        public void onEndpointLost(@NonNull String id) {
            JSObject d = new JSObject();
            d.put("id", id);
            notifyListeners("lost", d);
        }
    };

    private final ConnectionLifecycleCallback lifecycle = new ConnectionLifecycleCallback() {
        @Override
        public void onConnectionInitiated(@NonNull String id, @NonNull ConnectionInfo info) {
            client.acceptConnection(id, payloads);
        }

        @Override
        public void onConnectionResult(@NonNull String id, @NonNull ConnectionResolution res) {
            JSObject d = new JSObject();
            d.put("id", id);
            if (res.getStatus().isSuccess()) {
                peer = id;
                client.stopAdvertising();
                client.stopDiscovery();
                notifyListeners("connected", d);
            } else {
                d.put("reason", res.getStatus().getStatusMessage());
                notifyListeners("failed", d);
            }
        }

        @Override
        public void onDisconnected(@NonNull String id) {
            if (id.equals(peer)) peer = null;
            JSObject d = new JSObject();
            d.put("id", id);
            notifyListeners("disconnected", d);
        }
    };

    private final PayloadCallback payloads = new PayloadCallback() {
        @Override
        public void onPayloadReceived(@NonNull String id, @NonNull Payload p) {
            if (p.getType() != Payload.Type.BYTES || p.asBytes() == null) return;
            JSObject d = new JSObject();
            d.put("data", new String(p.asBytes(), StandardCharsets.UTF_8));
            notifyListeners("message", d);
        }

        @Override
        public void onPayloadTransferUpdate(@NonNull String id, @NonNull PayloadTransferUpdate u) {}
    };
}
