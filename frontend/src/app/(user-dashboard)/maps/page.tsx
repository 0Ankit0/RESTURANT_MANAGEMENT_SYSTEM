'use client';

import { useState } from 'react';
import Link from 'next/link';
import { ExternalLink, Globe, MapPinned, Navigation, Satellite } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useMapConfig } from '@/hooks/use-system';

function buildOsmEmbedUrl(latitude: number, longitude: number) {
  const delta = 0.02;
  const left = longitude - delta;
  const right = longitude + delta;
  const top = latitude + delta;
  const bottom = latitude - delta;

  return `https://www.openstreetmap.org/export/embed.html?bbox=${left}%2C${bottom}%2C${right}%2C${top}&layer=mapnik&marker=${latitude}%2C${longitude}`;
}

function buildGoogleEmbedUrl({
  apiKey,
  latitude,
  longitude,
  query,
}: {
  apiKey: string;
  latitude: number;
  longitude: number;
  query: string;
}) {
  const target = query.trim() || `${latitude},${longitude}`;
  return `https://www.google.com/maps/embed/v1/place?key=${encodeURIComponent(apiKey)}&q=${encodeURIComponent(target)}`;
}

export default function MapsPage() {
  const { data: mapConfig, isLoading } = useMapConfig();
  const [selectedProvider, setSelectedProvider] = useState<'osm' | 'google'>('osm');
  const [query, setQuery] = useState('Kathmandu Durbar Square');
  const [latitude, setLatitude] = useState('27.7049');
  const [longitude, setLongitude] = useState('85.3075');

  const numericLatitude = Number.parseFloat(latitude) || mapConfig?.default_center.latitude || 27.7172;
  const numericLongitude = Number.parseFloat(longitude) || mapConfig?.default_center.longitude || 85.3240;

  const providers = mapConfig
    ? (['osm', 'google'] as const).filter((provider) => mapConfig.providers[provider].enabled)
    : [];

  const activeProvider =
    providers.includes(selectedProvider) ? selectedProvider : (mapConfig?.provider ?? providers[0] ?? 'osm');

  const embedUrl =
    mapConfig && activeProvider === 'google' && mapConfig.providers.google.api_key
      ? buildGoogleEmbedUrl({
          apiKey: mapConfig.providers.google.api_key,
          latitude: numericLatitude,
          longitude: numericLongitude,
          query,
        })
      : buildOsmEmbedUrl(numericLatitude, numericLongitude);

  const externalUrl =
    activeProvider === 'google'
      ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query.trim() || `${numericLatitude},${numericLongitude}`)}`
      : `https://www.openstreetmap.org/?mlat=${numericLatitude}&mlon=${numericLongitude}#map=${mapConfig?.default_center.zoom ?? 13}/${numericLatitude}/${numericLongitude}`;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Maps</h1>
          <p className="text-gray-500">Loading provider configuration...</p>
        </div>
      </div>
    );
  }

  if (!mapConfig?.enabled) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Maps</h1>
          <p className="text-gray-500">Map integrations are disabled for this environment.</p>
        </div>

        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="pt-6">
            <p className="text-sm font-medium text-amber-800">Maps are currently unavailable.</p>
            <p className="mt-1 text-xs text-amber-700">
              Enable `FEATURE_MAPS=True` in your environment and then turn on either
              `OSM_MAPS_ENABLED` or `GOOGLE_MAPS_ENABLED`.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Maps</h1>
        <p className="text-gray-500">
          Preview OpenStreetMap and Google Maps integrations based on the providers enabled in this environment.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MapPinned className="h-5 w-5" />
              Provider Controls
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-5">
            <div>
              <p className="text-sm font-medium text-gray-900">Available providers</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {providers.map((provider) => (
                  <button
                    key={provider}
                    type="button"
                    onClick={() => setSelectedProvider(provider)}
                    className={`rounded-full px-3 py-1.5 text-sm font-medium transition-colors ${
                      activeProvider === provider
                        ? 'bg-blue-50 text-blue-600'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                    }`}
                  >
                    {mapConfig.providers[provider].label}
                  </button>
                ))}
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-2">
                <span className="text-sm font-medium text-gray-700">Latitude</span>
                <input
                  value={latitude}
                  onChange={(event) => setLatitude(event.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </label>
              <label className="space-y-2">
                <span className="text-sm font-medium text-gray-700">Longitude</span>
                <input
                  value={longitude}
                  onChange={(event) => setLongitude(event.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </label>
            </div>

            <label className="space-y-2">
              <span className="text-sm font-medium text-gray-700">Place label or search query</span>
              <input
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Kathmandu Durbar Square"
              />
            </label>

            <div className="rounded-2xl border border-gray-200 bg-gray-50 p-4">
              <p className="text-sm font-semibold text-gray-900">Environment gating</p>
              <div className="mt-3 space-y-2 text-xs text-gray-600">
                <p>
                  Active provider:
                  <span className="ml-1 font-medium text-gray-900">
                    {mapConfig.provider ? mapConfig.providers[mapConfig.provider].label : 'None'}
                  </span>
                </p>
                <p>
                  OSM:
                  <span className="ml-1 font-medium text-gray-900">
                    {mapConfig.providers.osm.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </p>
                <p>
                  Google Maps:
                  <span className="ml-1 font-medium text-gray-900">
                    {mapConfig.providers.google.enabled ? 'Enabled' : 'Disabled'}
                  </span>
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-3">
              <Link href={externalUrl} target="_blank">
                <Button variant="outline">
                  <ExternalLink className="mr-2 h-4 w-4" />
                  Open externally
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              {activeProvider === 'google' ? <Satellite className="h-5 w-5" /> : <Globe className="h-5 w-5" />}
              {activeProvider === 'google' ? 'Google Maps Preview' : 'OpenStreetMap Preview'}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white">
              <iframe
                key={`${activeProvider}-${embedUrl}`}
                title={`${activeProvider}-map`}
                src={embedUrl}
                className="h-[520px] w-full border-0"
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
              />
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-gray-200 bg-white p-4">
                <p className="flex items-center gap-2 text-sm font-semibold text-gray-900">
                  <Navigation className="h-4 w-4 text-blue-600" />
                  Current location
                </p>
                <p className="mt-2 text-sm text-gray-600">{query || 'Custom coordinate preview'}</p>
                <p className="mt-1 text-xs text-gray-500">
                  {numericLatitude.toFixed(5)}, {numericLongitude.toFixed(5)}
                </p>
              </div>

              <div className="rounded-2xl border border-gray-200 bg-white p-4">
                <p className="text-sm font-semibold text-gray-900">Integration notes</p>
                <p className="mt-2 text-xs text-gray-500">
                  OpenStreetMap works without an API key. Google Maps appears only when both
                  `FEATURE_MAPS=True` and a valid `GOOGLE_MAPS_API_KEY` are configured.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
