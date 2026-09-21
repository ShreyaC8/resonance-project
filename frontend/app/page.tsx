"use client";

import { useEffect, useState } from "react";
import TasteMap from "@/components/TasteMap";

type Track = {
    track_id: string;
    track_name: string;
    artists: string;
    genre: string;
    cluster: number;
    x: number;
    y: number;
};

type SearchTrack = {
  track_id: string;
  track_name: string;
  artists: string;
};

export default function Home() {
    const [tracks, setTracks] = useState<Track[]>([]);
    const [userPosition, setUserPosition] = useState<{ x: number; y: number } | null>(null);
    
    const [search, setSearch] = useState("");
    const [searchResults, setSearchResults] = useState<SearchTrack[]>([]);
    const [selectedTracks, setSelectedTracks] = useState<SearchTrack[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(
            `http://127.0.0.1:8000/taste-map?seed_tracks=5SuOikwiRyPMVoIQDJUgSV,4qPNDBW1i3p13qLCt0Ki3A,1iJBSr7s7jYXzM8EGcbK5b`
        )
            .then((response) => response.json())
            .then((data) => {
                setTracks(data.tracks);
                setUserPosition(data.user_position);
                setLoading(false);
        });
    }, []);

    useEffect(() => {
        if (search.trim().length < 2 ) {
            setSearchResults([]);
            return;
        }

        fetch(
            `http://127.0.0.1:8000/tracks/search?q=${encodeURIComponent(search)}`
        )
            .then((response) => response.json())
            .then((data) => {
                setSearchResults(data);
            });
    }, [search]);

    function selectTrack(track: SearchTrack) {
        if (selectedTracks.some((t) => t.track_id === track.track_id)) {
            return;
        }

        const updatedTracks = [...selectedTracks, track];

        setSelectedTracks(updatedTracks);
        setSearch("");
        setSearchResults([]);

        updateTasteMap(updatedTracks);
    }

    function removeTrack(trackId: string) {
        const updatedTracks = selectedTracks.filter(
            (track) => track.track_id !== trackId
        );

        setSelectedTracks(updatedTracks);

        if (updatedTracks.length > 0) {
            updateTasteMap(updatedTracks);
        }
    }    
    
    function updateTasteMap(seedTracks: SearchTrack[]) {
        const ids = seedTracks.map((track) => track.track_id).join(",");

        fetch(`http://127.0.0.1:8000/taste-map?seed_tracks=${ids}`)
            .then((response) => response.json())
            .then((data) => {
                setTracks(data.tracks);
                setUserPosition(data.user_position)
            });
    }

    if (loading) {
        return <p>Loading your musical universe...</p>;
    }

    return (
        <main>
            <h1>Your Musical Universe</h1>

            <div style={{ marginBottom: "30px" }}>
                <input
                    type="text"
                    placeholder="Search for a song..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    style={{
                        width: "400px",
                        padding: "10px",
                        fontSize: "16px"
                    }}
                />

                {searchResults.length > 0 && (
                    <div
                        style={{
                            width: "400px",
                            border: "1px solid #ccc",
                            marginTop: "5px"
                        }}
                    >
                        {searchResults.map((track) => (
                            <button
                                key={track.track_id}
                                onClick={() => selectTrack(track)}
                                style={{
                                    display: "block",
                                    width: "100%",
                                    padding: "10px",
                                    textAlign: "left",
                                    border: "none",
                                    background: "white",
                                    cursor: "pointer"
                                }}
                            >
                                {track.track_name} = {track.artists}
                            </button>
                        ))}
                    </div>
                )}

                {selectedTracks.length > 0 && (
                    <div style={{ marginTop: "20px" }}>
                        <h3>Your seeds</h3>

                        {selectedTracks.map((track) => (
                            <div key={track.track_id}>
                                {track.track_name} - {track.artists}

                                <button onClick={() => removeTrack(track.track_id)}>
                                    x
                                </button>
                            </div>
                        ))}
                    </div>    
                )}
            </div>
        
        <TasteMap 
            tracks={tracks}
            userPosition={userPosition}   
            />
        </main>
    );
}