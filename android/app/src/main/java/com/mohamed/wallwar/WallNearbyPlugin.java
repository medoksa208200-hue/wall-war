package com.mohamed.wallwar;

import android.Manifest;
import android.os.Build;
import androidx.annotation.NonNull;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
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
import java.util.List;

/**
 * Two-phone play over Bluetooth / Wi-Fi Direct with Google Nearby Connections — no internet needed.
 * JS: ensure() → advertise({name}) on the host, discover() + connect({id,name}) on the guest,
 * then send({data}) and listen for found / lost / connected / failed / disconnected / message.
 */
@CapacitorPlugin(
    name = "WallNearby",
    permissions = {
        @Permission(alias = "location", strings = { Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION }),
        @Permission(alias = "bluetooth", strings = { Manifest.permission.BLUETOOTH_SCAN, Manifest.permission.BLUETOOTH_ADVERTISE, Manifest.permission.BLUETOOTH_CONNECT }),
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

    private String[] neededAliases() {
        List<String> a = new ArrayList<>();
        a.add("location");
        if (Build.VERSION.SDK_INT >= 31) a.add("bluetooth");
        if (Build.VERSION.SDK_INT >= 33) a.add("wifi");
        return a.toArray(new String[0]);
    }

    private boolean allGranted() {
        for (String alias : neededAliases()) {
            if (getPermissionState(alias) != PermissionState.GRANTED) return false;
        }
        return true;
    }

    @PluginMethod
    public void ensure(PluginCall call) {
        if (allGranted()) {
            JSObject r = new JSObject();
            r.put("granted", true);
            call.resolve(r);
            return;
        }
        requestPermissionForAliases(neededAliases(), call, "permsDone");
    }

    @PermissionCallback
    private void permsDone(PluginCall call) {
        JSObject r = new JSObject();
        r.put("granted", allGranted());
        call.resolve(r);
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
