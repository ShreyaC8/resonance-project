'''def get_recommendations(request: RecRequest):
    track_ids = []
    recommendations = []
    response = []

    for track in request.tracks:
        track_ids.append(track.track_id)

    with SessionLocal() as db:
        seed_tracks = db.execute(select(Track).where(Track.track_id.in_(track_ids))).scalars().all()
        profile = calculate_profile(seed_tracks)

        all_tracks = db.execute(select(Track)).scalars().all()
        for track in all_tracks:
            #Ensure entered tracks do not appear as recommendations
            if track.track_id in track_ids:
                continue

            difference, similarity = calculate_similarity(track, profile)
            description = similarity_description(difference)
            recommendations.append((track, similarity, description))
        
        recommendations.sort(reverse=True, key=key_helper)
        recommendations = recommendations[:request.limit]
        
        if not recommendations:
            return 'No tracks recommended'
                
        for (track, similarity, description) in recommendations:
            response.append({
                "track_id": track.track_id,
                "track_name": track.track_name,
                "artists": track.artists,
                "score": similarity,
                "reason": description
            })
                
        return response    
'''

'''
    recommendations = []
    response = []
    statement = select(Track)

     Method to compare genre can be more sophisticated 
    (e.g. pop fans may enjoy indie pop)
    Maybe use string matching to filter related genres as an improvement
    if request.genre is not None:
        statement = statement.filter(Track.track_genre == request.genre)

    with SessionLocal() as db:
        tracks = db.execute(statement).scalars().all()
        for track in tracks:
            This section requires weighting to improve recommendation predictions
            score = 0

            if request.energy is not None:
                score += abs(track.energy - request.energy)

            if request.danceability is not None:
                score += abs(track.danceability - request.danceability)

            if request.valence is not None:
                score += abs(track.valence - request.valence)

            #Popularity needs to be normalised from 0-100 to 0-1
            if request.popularity is not None:
                score += 0.01*abs(track.popularity - request.popularity)

            recommendations.append((track, score))

        recommendations.sort(key=key_helper)
        recommendations = recommendations[:request.limit]

        if not recommendations:
            return 'No tracks recommended'
        
        for (track, score) in recommendations:
            response.append({
                "track_id": track.track_id,
                "track_name": track.track_name,
                "artists": track.artists,
                "score": score
            })
        
        return response
'''