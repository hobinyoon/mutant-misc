#pragma once

#include <fstream>
#include <string>
#include <boost/filesystem.hpp>
#include <boost/format.hpp>

#include "cons.h"
#include "util.h"

namespace Stat {
	template<class T> void ByRank(const std::vector<T>& v1, std::ofstream& ofs) {
		if (v1.size() == 0) {
			Cons::P("No input to generate stat.");
			return;
		}

		std::vector<T> v(v1);
		sort(v.begin(), v.end());

		T  min = *(v.begin());
		T  max = *(v.rbegin());
		T  _1p = v[size_t(0.01 * (v.size() - 1))];
		T  _5p = v[size_t(0.05 * (v.size() - 1))];
		T _10p = v[size_t(0.10 * (v.size() - 1))];
		T _25p = v[size_t(0.25 * (v.size() - 1))];
		T _50p = v[size_t(0.50 * (v.size() - 1))];
		T _75p = v[size_t(0.75 * (v.size() - 1))];
		T _90p = v[size_t(0.90 * (v.size() - 1))];
		T _95p = v[size_t(0.95 * (v.size() - 1))];
		T _99p = v[size_t(0.99 * (v.size() - 1))];

		double sum = 0.0;
		double sum_sq = 0.0;
		for (T e: v) {
			sum += e;
			sum_sq += (e * e);
		}
		double avg = sum / v.size();
		double sd = sqrt(sum_sq / v.size() - avg * avg);
		std::string stat = str(boost::format(
					"avg %s" "\nsd  %s" "\nmin %s" "\nmax %s"
					"\n 1p %s" "\n 5p %s" "\n10p %s" "\n25p %s" "\n50p %s" "\n75p %s" "\n90p %s" "\n95p %s" "\n99p %s")
				% avg % sd % min % max
				% _1p % _5p % _10p % _25p % _50p % _75p % _90p % _95p % _99p
				);
		//Cons::P(stat);

		ofs << Util::Prepend("# ", stat);
		ofs << "\n";
		ofs << "# rank value\n";

		sort(v.begin(), v.end(), std::greater<int>());

		for (size_t i = 0; i < v.size(); i ++) {
			// Always print the first and last (rank, value)
			if (i == 0 || i == (v.size() - 1)) {
				ofs << i << " " << v[i] << "\n";
			}
			// Skip, if the value is the same as the previous and the next. It helps
			// reduce the plot size.
			else if (v[i - 1] == v[i] && v[i] == v[i + 1]) {
			}
			else {
				ofs << i << " " << v[i] << "\n";
			}
		}
	}

	template<class T> void GenCDF(const std::vector<T>& v1, std::ofstream& ofs) {
		if (v1.size() == 0) {
			Cons::P("No input to generate stat.");
			return;
		}

		std::vector<T> v(v1);
		sort(v.begin(), v.end());

		T  min = *(v.begin());
		T  max = *(v.rbegin());
		T  _1p = v[size_t(0.01 * (v.size() - 1))];
		T  _5p = v[size_t(0.05 * (v.size() - 1))];
		T _10p = v[size_t(0.10 * (v.size() - 1))];
		T _25p = v[size_t(0.25 * (v.size() - 1))];
		T _50p = v[size_t(0.50 * (v.size() - 1))];
		T _75p = v[size_t(0.75 * (v.size() - 1))];
		T _90p = v[size_t(0.90 * (v.size() - 1))];
		T _95p = v[size_t(0.95 * (v.size() - 1))];
		T _99p = v[size_t(0.99 * (v.size() - 1))];

		double sum = 0.0;
		double sum_sq = 0.0;
		for (T e: v) {
			sum += e;
			sum_sq += (e * e);
		}
		double avg = sum / v.size();
		double sd = sqrt(sum_sq / v.size() - avg * avg);
		std::string stat = str(boost::format(
					"num_items %d"
					"\navg %s" "\nsd  %s" "\nmin %s" "\nmax %s"
					"\n 1p %s" "\n 5p %s" "\n10p %s" "\n25p %s" "\n50p %s" "\n75p %s" "\n90p %s" "\n95p %s" "\n99p %s")
				% v.size()
				% avg % sd % min % max
				% _1p % _5p % _10p % _25p % _50p % _75p % _90p % _95p % _99p
				);
		//Cons::P(stat);

		ofs << Util::Prepend("# ", stat);
		ofs << "\n";
		for (size_t i = 0; i < v.size(); i ++) {
			// Note: rewrite following the above logic.
			if (0 < i && i < (v.size() - 1) && v[i - 1] == v[i] && v[i] == v[i + 1])
				continue;
			ofs << v[i] << " " << (double(i) / v.size()) << "\n";
		}
		// Print the last value twice to make the last Y value 1.0
		ofs << *v.rbegin() << " 1.0\n";
	}
};
