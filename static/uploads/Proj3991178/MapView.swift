//
//  MapView.swift
//  BeatGenerator
//
//  Created by Praveer Sharan on 11/6/22.
//

import Foundation
import SwiftUI
import MapKit

struct MapView: View {
    @State private var region = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 34.011_286, longitude: -116.166_868),
        span: MKCoordinateSpan(latitudeDelta: 0.2, longitudeDelta: 0.2)
    )
    var F: Double
    var body: some View {
        VStack {
            Map(coordinateRegion: $region)
                .ignoresSafeArea(edges: .top)

            CircleImage()
                .offset(y: -130)
                .padding(.bottom, -130)

            VStack(alignment: .leading) {
                Text("Turtle Rock")
                    .font(.title)
                    .foregroundColor(Color.init(red: 100/255, green: 150/255, blue: 255/255))

                HStack {
                    Text("Joshua Tree National Park")
                    Spacer()
                    Text("California")
                }
                .font(.subheadline)
                .foregroundColor(.secondary)

                Divider()

                Text("About Turtle Rock")
                    .font(.title2)
                Text("This towering outcropping of Entrada Sandstone, the same tye of rock that forms arches in Arches National Park, is known as Turtle Rock. Fahrenheit is: " + String(F))
                Divider()
            }
            .padding()

            Spacer()
        }
    }
}

struct MapView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            MapView(F:Double())
        }
    }
}
